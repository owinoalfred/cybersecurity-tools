
        $ErrorActionPreference = 'Stop'
        try {
            cd 'Y:\projects\x\cyber\cybersecurity-tools'
            python -m tools.network.packet_sniffer --count 100 --format json --filter-protocol tcp
        } catch {
            Write-Host "Error: $_" -ForegroundColor Red
            exit 1
        }
        