"""Celery jobs: photo recognition and board solving."""

import os
import json
import logging
import tempfile
import shutil
import redis
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded
from sqlalchemy.orm import Session

from src.celery_app import celery_app
from src.config import settings
from src.db import SessionLocal
from src.models import Board, Turn
from src.s3 import download_file_from_s3
from inference.reconstruct_board import run_pipeline, run_hand_pipeline

logger = logging.getLogger(__name__)

# Initialize sync Redis client
try:
    redis_client = redis.from_url(
        settings.CELERY_BROKER_URL,
        decode_responses=True
    )
except Exception as e:
    logger.error("Failed to initialize Redis client: %s", e)

@celery_app.task(
    bind=True,
    name="src.tasks.process_board_image",
    max_retries=3,
    default_retry_delay=10,
)
def process_board_image(self, board_id: str):
    """Quick-play recognition: download board + hand, run ML, cache result.
    Updates the Board row and Redis envelope; client polls /next-play until done.
    Retries on transient S3 or DB errors with exponential backoff.
    """
    logger.info("Starting processing for board %s", board_id)

    # load board record and image paths
    session: Session = SessionLocal()
    board = None
    try:
        board = session.query(Board).filter(Board.id == board_id).first()
        if not board:
            logger.error("Board %s not found in database", board_id)
            return {"status": "error", "error": "Board not found"}

        image_path = board.image_path
        hand_image_path = board.hand_image_path
        if not image_path:
            logger.error("Board %s has no board image path in database", board_id)
            return {"status": "error", "error": "No board image path"}
        if not hand_image_path:
            logger.error("Board %s has no hand image path in database", board_id)
            return {"status": "error", "error": "No hand image path"}
    except Exception as e:
        logger.error("Database connection/query error: %s", e)
        try:
            retry_delay = 10 * (3 ** self.request.retries)
            raise self.retry(exc=e, countdown=retry_delay)
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for board %s due to DB error", board_id)
            raise
    finally:
        session.close()

    temp_dir = tempfile.mkdtemp()
    temp_image_path = os.path.join(temp_dir, os.path.basename(image_path))
    temp_hand_image_path = os.path.join(temp_dir, os.path.basename(hand_image_path))
    temp_out_dir = os.path.join(temp_dir, "output")

    try:
        # download from S3
        try:
            download_file_from_s3(image_path, temp_image_path)
        except Exception as e:
            logger.error("Failed to download board image %s from S3: %s", image_path, e)
            try:
                retry_delay = 10 * (3 ** self.request.retries)
                raise self.retry(exc=e, countdown=retry_delay)
            except MaxRetriesExceededError:
                logger.error("Max retries exceeded for board %s due to S3 board download failure", board_id)
                raise

        # Download hand image
        try:
            download_file_from_s3(hand_image_path, temp_hand_image_path)
        except Exception as e:
            logger.error("Failed to download hand image %s from S3: %s", hand_image_path, e)
            try:
                retry_delay = 10 * (3 ** self.request.retries)
                raise self.retry(exc=e, countdown=retry_delay)
            except MaxRetriesExceededError:
                logger.error("Max retries exceeded for board %s due to S3 hand download failure", board_id)
                raise

        logger.info("Executing ML inference on board and hand %s...", board_id)
        models_dir = os.path.abspath(settings.MODELS_DIR)

        try:
            # Run board pipeline
            board_state = run_pipeline(
                image_path=temp_image_path,
                out_dir=temp_out_dir,
                models_dir=models_dir,
                conf=0.25
            )

            # Run hand pipeline
            hand_state = run_hand_pipeline(
                image_path=temp_hand_image_path,
                models_dir=models_dir,
                conf=0.25
            )
            
            combined_result = {
                **board_state,
                "hand": hand_state
            }

            # Success writes
            success_envelope = {
                "id": board_id,
                "status": "completed",
                "result": combined_result,
                "error": None
            }
            try:
                redis_client.set(f"boards:{board_id}", json.dumps(success_envelope), ex=settings.REDIS_TTL_SECONDS)
                logger.info("Saved completed status to Redis for board %s", board_id)
            except Exception as e:
                logger.error("Failed to write completed status to Redis for board %s: %s", board_id, e)

            session = SessionLocal()
            try:
                board = session.query(Board).filter(Board.id == board_id).first()
                if board:
                    board.status = "completed"
                    board.classification_results = board_state
                    board.hand_results = hand_state
                    board.failure_code = None
                    board.failure_message = None
                    session.add(board)
                    session.commit()
                    logger.info("Updated database record for board %s to completed", board_id)
            except Exception as e:
                logger.error("Failed to update DB for board %s: %s", board_id, e)
                try:
                    retry_delay = 10 * (3 ** self.request.retries)
                    raise self.retry(exc=e, countdown=retry_delay)
                except MaxRetriesExceededError:
                    raise
            finally:
                session.close()

            return success_envelope

        except SoftTimeLimitExceeded:
            logger.error("Processing timed out for board %s", board_id)
            error_code = "PROCESSING_TIMED_OUT"
            error_msg = "Processing took too long and was stopped. Please try again."
        except Exception as e:
            logger.error("Inference failure for board %s: %s", board_id, e)
            error_code = "INFERENCE_ERROR"
            error_msg = f"Image processing failed: {str(e)}"

        # Failure writes
        error_envelope = {
            "id": board_id,
            "status": "failed",
            "result": None,
            "error": {"code": error_code, "message": error_msg}
        }
        try:
            redis_client.set(f"boards:{board_id}", json.dumps(error_envelope), ex=settings.REDIS_TTL_SECONDS)
            logger.info("Saved failed status to Redis for board %s", board_id)
        except Exception as redis_err:
            logger.error("Failed to write failed status to Redis for board %s: %s", board_id, redis_err)

        session = SessionLocal()
        try:
            board = session.query(Board).filter(Board.id == board_id).first()
            if board:
                board.status = "failed"
                board.failure_code = error_code
                board.failure_message = error_msg
                # Do not write to classification_results on failure
                session.add(board)
                session.commit()
                logger.info("Updated database record for board %s to failed", board_id)
        except Exception as db_err:
            logger.error("Failed to write failed status to DB for board %s: %s", board_id, db_err)
        finally:
            session.close()

        return error_envelope

    finally:
        try:
            shutil.rmtree(temp_dir)
            logger.debug("Cleaned up temp directory %s", temp_dir)
        except Exception as e:
            logger.warning("Failed to remove temp directory %s: %s", temp_dir, e)

@celery_app.task(
    bind=True,
    name="src.tasks.process_turn_image",
    max_retries=3,
    default_retry_delay=10,
)
def process_turn_image(self, turn_id: str):
    """Recognition for a saved-game turn: same ML pipeline as quick-play.
    Writes combined board + hand JSON into turn.results and sets status to
    finished_processing (or failed on inference error).
    """
    logger.info("Starting processing for turn %s", turn_id)

    session: Session = SessionLocal()
    turn = None
    try:
        turn = session.query(Turn).filter(Turn.id == turn_id).first()
        if not turn:
            logger.error("Turn %s not found in database", turn_id)
            return {"status": "error", "error": "Turn not found"}

        image_path = turn.board_image_url
        hand_image_path = turn.hand_image_url
        if not image_path or not hand_image_path:
            return {"status": "error", "error": "Missing image paths"}
            
    except Exception as e:
        logger.error("Database error: %s", e)
        try:
            raise self.retry(exc=e, countdown=10)
        except MaxRetriesExceededError:
            raise
    finally:
        session.close()

    temp_dir = tempfile.mkdtemp()
    temp_image_path = os.path.join(temp_dir, os.path.basename(image_path))
    temp_hand_image_path = os.path.join(temp_dir, os.path.basename(hand_image_path))
    temp_out_dir = os.path.join(temp_dir, "output")

    try:
        download_file_from_s3(image_path, temp_image_path)
        download_file_from_s3(hand_image_path, temp_hand_image_path)

        logger.info("Executing ML inference on turn %s...", turn_id)
        models_dir = os.path.abspath(settings.MODELS_DIR)

        board_state = run_pipeline(
            image_path=temp_image_path,
            out_dir=temp_out_dir,
            models_dir=models_dir,
            conf=0.25
        )

        hand_state = run_hand_pipeline(
            image_path=temp_hand_image_path,
            models_dir=models_dir,
            conf=0.25
        )
        
        combined_result = {
            **board_state,
            "hand": hand_state
        }

        session = SessionLocal()
        try:
            turn = session.query(Turn).filter(Turn.id == turn_id).first()
            if turn:
                turn.status = "finished_processing"
                turn.results = combined_result
                session.add(turn)
                session.commit()
                logger.info("Updated database record for turn %s to finished_processing", turn_id)
        finally:
            session.close()

        return combined_result

    except Exception as e:
        logger.error("Inference failure for turn %s: %s", turn_id, e)
        session = SessionLocal()
        try:
            turn = session.query(Turn).filter(Turn.id == turn_id).first()
            if turn:
                turn.status = "failed"
                turn.results = {"error": str(e)}
                session.add(turn)
                session.commit()
        finally:
            session.close()
        return {"error": str(e)}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def _handle_solver_failure(board_id: str, error_code: str, error_msg: str):
    """Mark a board solve as failed in Postgres and mirror that in Redis.
    Called when parsing or the solver itself fails so polling stops cleanly.
    """
    session = SessionLocal()
    try:
        board = session.query(Board).filter(Board.id == board_id).first()
        if board:
            board.status = "failed"
            board.solution = None
            board.failure_code = error_code
            board.failure_message = error_msg
            session.add(board)
            session.commit()
            
            # update redis
            try:
                redis_res = redis_client.get(f"boards:{board_id}")
                if redis_res:
                    bs = json.loads(redis_res)
                    bs["status"] = "failed"
                    bs["error"] = {"code": error_code, "message": error_msg}
                    redis_client.set(f"boards:{board_id}", json.dumps(bs), ex=settings.REDIS_TTL_SECONDS)
            except Exception:
                pass
    except Exception as e:
        logger.error("Failed to update failure state for board %s: %s", board_id, e)
    finally:
        session.close()

@celery_app.task(
    bind=True,
    name="src.tasks.solve_board_task",
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=15,
)
def solve_board_task(self, board_id: str):
    """Run most_cards_down on a quick-play board and store the solution.
    Prefers Redis for current sets/hand; fix_results overrides ML output.
    Writes solution to DB and extends the Redis envelope for /next-play.
    """
    logger.info("Starting solver for board %s", board_id)

    # board state: redis first, else DB
    board_state = None
    try:
        redis_res = redis_client.get(f"boards:{board_id}")
        if redis_res:
            board_state = json.loads(redis_res)
    except Exception as e:
        logger.warning("Failed to fetch from Redis for board %s: %s", board_id, e)
        
    session: Session = SessionLocal()
    try:
        board = session.query(Board).filter(Board.id == board_id).first()
        if not board:
            logger.error("Board %s not found in database", board_id)
            return {"status": "error", "error": "Board not found"}

        if not board_state:
            # Reconstruct board state from DB
            board_state = {
                "id": board_id,
                "status": board.status,
                "result": {}
            }
            if board.classification_results:
                board_state["result"] = dict(board.classification_results)
                
            if board.fix_results:
                # Override with corrections
                board_state["result"]["sets"] = board.fix_results.get("sets", [])
                board_state["result"]["unassigned"] = board.fix_results.get("unassigned", [])
                board_state["result"]["hand"] = board.fix_results.get("hand", [])
            elif board.hand_results:
                board_state["result"]["hand"] = board.hand_results.get("hand", [])
                
    except Exception as e:
        logger.error("Database connection/query error: %s", e)
        try:
            retry_delay = 10 * (3 ** self.request.retries)
            raise self.retry(exc=e, countdown=retry_delay)
        except MaxRetriesExceededError:
            raise
    finally:
        session.close()

    # 2. Extract sets and hand
    try:
        res = board_state.get("result", {})
        raw_sets = res.get("sets", [])
        raw_hand = res.get("hand", [])
        
        # API tiles -> solver (n, c) format
        def map_tile(t: dict) -> dict:
            color_map = {"black": "k", "blue": "b", "red": "r", "orange": "o", "joker": "j"}
            n_val = str(t.get("number")).lower()
            if n_val == "joker":
                n_val = "j"
            else:
                n_val = int(n_val)
            col_val = str(t.get("color", "")).lower()
            c_val = color_map.get(col_val, "j") if col_val != "joker" else "j"
            if n_val == "j" or c_val == "j":
                n_val = "j"
                c_val = "j"
            return {"n": n_val, "c": c_val}
            
        solver_board = [[map_tile(t) for t in s.get("tiles", [])] for s in raw_sets]
        solver_hand = [map_tile(t) for t in raw_hand]
    except Exception as e:
        logger.error("Failed to parse board state for solver: %s", e)
        _handle_solver_failure(board_id, "PARSE_ERROR", f"Failed to parse board state: {e}")
        return
        
    # 3. Call solver
    try:
        from src.rummikub_solver import most_cards_down
        play_obj = most_cards_down(solver_board, solver_hand)
        solution_dict = play_obj.to_dict()
    except SoftTimeLimitExceeded:
        logger.error("Solver timed out for board %s", board_id)
        _handle_solver_failure(board_id, "TIMEOUT", "Solver took too long to complete")
        return
    except Exception as e:
        logger.error("Solver failed for board %s: %s", board_id, e)
        _handle_solver_failure(board_id, "SOLVER_ERROR", f"Algorithm failed: {e}")
        return
        
    # 4. Save solution to DB
    session = SessionLocal()
    try:
        board = session.query(Board).filter(Board.id == board_id).first()
        if board:
            board.solution = solution_dict
            session.add(board)
            session.commit()
            logger.info("Saved solution to DB for board %s", board_id)
            
            # Update Redis as well
            board_state["solution"] = solution_dict
            try:
                redis_client.set(f"boards:{board_id}", json.dumps(board_state), ex=settings.REDIS_TTL_SECONDS)
            except Exception:
                pass
    except Exception as e:
        logger.error("Failed to save solution to DB for board %s: %s", board_id, e)
        try:
            retry_delay = 10 * (3 ** self.request.retries)
            raise self.retry(exc=e, countdown=retry_delay)
        except MaxRetriesExceededError:
            raise
    finally:
        session.close()

@celery_app.task(
    bind=True,
    name="src.tasks.solve_turn_task",
    max_retries=3,
    default_retry_delay=10,
    soft_time_limit=15,
)
def solve_turn_task(self, turn_id: str):
    """Run the solver on a saved turn's approved results.
    first_drop turns use solve_first_drop (30+ opening meld); others use
    most_cards_down. Updates turn.status to solved or failed.
    """
    logger.info("Starting solver for turn %s", turn_id)

    session: Session = SessionLocal()
    try:
        turn = session.query(Turn).filter(Turn.id == turn_id).first()
        if not turn:
            logger.error("Turn %s not found in database", turn_id)
            return {"status": "error", "error": "Turn not found"}

        original_results = turn.results or {}
        raw_sets = original_results.get("sets", [])
        raw_hand = original_results.get("hand", [])

        # API tiles -> solver (n, c) format
        def map_tile(t: dict) -> dict:
            color_map = {"black": "k", "blue": "b", "red": "r", "orange": "o", "joker": "j"}
            n_val = str(t.get("number", "0")).lower()
            if n_val == "joker":
                n_val = "j"
            else:
                try:
                    n_val = int(n_val)
                except ValueError:
                    n_val = "j"
            col_val = str(t.get("color", "")).lower()
            c_val = color_map.get(col_val, "j") if col_val != "joker" else "j"
            if n_val == "j" or c_val == "j":
                n_val = "j"
                c_val = "j"
            return {"n": n_val, "c": c_val}
            
        solver_board = [[map_tile(t) for t in s.get("tiles", [])] for s in raw_sets]
        solver_hand = [map_tile(t) for t in raw_hand]

        # first drop vs normal solve
        if turn.is_first_drop:
            from src.rummikub_solver import first_drop_play
            play = first_drop_play(solver_hand)
            solution_dict = {
                "placed": play["placed"],
                "new_board": solver_board + play["new_melds"],
                "count": play["count"],
                "is_draw": play["is_draw"],
                "first_drop": True,
                "points": play["points"],
            }
        else:
            from src.rummikub_solver import most_cards_down
            play_obj = most_cards_down(solver_board, solver_hand)
            solution_dict = play_obj.to_dict()

        mock_results = {
            "status": "success",
            "sets": original_results.get("sets", []),
            "unassigned": original_results.get("unassigned", []),
            "hand": original_results.get("hand", []),
            "solution": solution_dict
        }
        
        turn.status = "solved"
        turn.results = mock_results
        session.add(turn)
        session.commit()
        logger.info("Updated database record for turn %s to solved", turn_id)
        return mock_results

    except SoftTimeLimitExceeded:
        logger.error("Solver timed out for turn %s", turn_id)
        try:
            turn = session.query(Turn).filter(Turn.id == turn_id).first()
            if turn:
                turn.status = "failed"
                turn.results = {"error": "Solver took too long to complete"}
                session.add(turn)
                session.commit()
        except Exception:
            pass
        return {"error": "Solver took too long to complete"}
    except Exception as e:
        logger.error("Solver failure for turn %s: %s", turn_id, e)
        session.rollback()
        try:
            # Transition to failed state on error
            turn = session.query(Turn).filter(Turn.id == turn_id).first()
            if turn:
                turn.status = "failed"
                turn.results = {"error": str(e)}
                session.add(turn)
                session.commit()
                logger.info("Updated database record for turn %s to failed", turn_id)
        except Exception as inner_e:
            logger.error("Failed to update status to failed for turn %s: %s", turn_id, inner_e)
        return {"error": str(e)}
    finally:
        session.close()
