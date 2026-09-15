param(
    [Parameter(Mandatory = $true)]
    [string]$Code,
    [int]$Port = 9876
)

$client = [System.Net.Sockets.TcpClient]::new()
try {
    $client.Connect('127.0.0.1', $Port)
    $client.ReceiveTimeout = 180000
    $client.SendTimeout = 10000
    $stream = $client.GetStream()
    $payload = @{
        type = 'execute_code'
        params = @{ code = $Code }
    } | ConvertTo-Json -Depth 8 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Flush()

    $buffer = New-Object byte[] 65536
    $builder = [System.Text.StringBuilder]::new()
    while ($true) {
        $read = $stream.Read($buffer, 0, $buffer.Length)
        if ($read -le 0) { break }
        [void]$builder.Append([System.Text.Encoding]::UTF8.GetString($buffer, 0, $read))
        try {
            $parsed = $builder.ToString() | ConvertFrom-Json -ErrorAction Stop
            $parsed | ConvertTo-Json -Depth 12
            break
        } catch {
            continue
        }
    }
} finally {
    $client.Dispose()
}
