function Get-LanIpAddress {
    $configs = Get-CimInstance Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True" -ErrorAction SilentlyContinue
    if ($configs) {
        foreach ($config in $configs) {
            if ($null -eq $config.DefaultIPGateway -or $config.DefaultIPGateway.Count -eq 0) {
                continue
            }

            foreach ($ip in $config.IPAddress) {
                if ($ip -match '^192\.168\.1\.\d+$' -and $ip -ne '192.168.1.1') {
                    return $ip
                }
            }
        }
    }

    $ipconfig = ipconfig
    $matches = [regex]::Matches($ipconfig, '192\.168\.1\.\d+')
    foreach ($match in $matches) {
        $ip = $match.Value
        if ($ip -ne '192.168.1.1') {
            return $ip
        }
    }

    return $null
}

Get-LanIpAddress
