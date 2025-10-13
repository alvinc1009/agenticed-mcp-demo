PS C:\Windows\System32> $session
7d61ebff-bca4-4007-9e04-1561596b2f14
PS C:\Windows\System32> $pub = "https://agenticed-mcp-demo.onrender.com"
PS C:\Windows\System32>
PS C:\Windows\System32> # Health/version
PS C:\Windows\System32> Invoke-WebRequest "$pub/health" | % { $_.StatusCode, $_.Content }
200
{"ok":true}
PS C:\Windows\System32> Invoke-WebRequest "$pub/version" | % { $_.StatusCode, $_.Content }
200
agenticed-mcp-demo / fastmcp 2.12.1 / mcp 1.16.0
PS C:\Windows\System32>
PS C:\Windows\System32> # GET /mcp should be 405 (Method Not Allowed), NOT 500
PS C:\Windows\System32> Invoke-WebRequest "$pub/mcp" -Method GET | % { $_.StatusCode }
Invoke-WebRequest: Internal Server Error
PS C:\Windows\System32> $hdrs = @{ Accept="application/json, text/event-stream"; "Content-Type"="application/json" }
PS C:\Windows\System32>
PS C:\Windows\System32> try {
>>   $init = Invoke-WebRequest -Uri "$pub/mcp" -Method POST -Headers $hdrs -Body @'
>> {"jsonrpc":"2.0","id":"1","method":"initialize","params":{
>>   "protocolVersion":"2024-11-05",
>>   "clientInfo":{"name":"ps","version":"1.0"},
>>   "capabilities":{}
>> }}
>> '@
>>   "STATUS: $($init.StatusCode)"
>>   $init.Headers.GetEnumerator() | Format-List
>>   $init.Content
>> } catch {
>>   $resp = $_.Exception.Response
>>   if ($resp -ne $null) {
>>     $sr = New-Object IO.StreamReader($resp.GetResponseStream())
>>     $body = $sr.ReadToEnd()
>>     "STATUS: $($resp.StatusCode.value__) $($resp.StatusDescription)"
>>     "HEADERS:`n" + ($resp.Headers | Out-String)
>>     "BODY:`n$body"
>>   } else {
>>     "No response body was returned."
>>   }
>> }
InvalidOperation:
Line |
  15 |      $sr = New-Object IO.StreamReader($resp.GetResponseStream())
     |      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Method invocation failed because [System.Net.Http.HttpResponseMessage] does not contain a method named 'GetResponseStream'.
PS C:\Windows\System32>
