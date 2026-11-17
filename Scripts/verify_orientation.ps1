# Validate GPU screenshots of the asymmetric external NDI pattern.
Add-Type -AssemblyName System.Drawing
function Get-PanelColors([string]$Path) {
    $bitmap = [System.Drawing.Bitmap]::new($Path)
    try {
        $values = @()
        foreach ($band in @(250, 600)) {
            [double]$red = 0; [double]$blue = 0; $count = 0
            for ($x = 400; $x -lt 480; $x += 2) {
                for ($y = $band; $y -lt ($band + 60); $y += 2) {
                    $pixel = $bitmap.GetPixel($x, $y)
                    $red += $pixel.R; $blue += $pixel.B; $count++
                }
            }
            $values += @{ Red = $red / $count; Blue = $blue / $count }
        }
        return $values
    } finally { $bitmap.Dispose() }
}
$saved = Join-Path $PSScriptRoot '../Saved'
$before = Get-PanelColors (Join-Path $saved 'Orientation-Before.png')
$after = Get-PanelColors (Join-Path $saved 'Orientation-After.png')
if (-not ($before[0].Blue -gt $before[0].Red * 3 -and $before[1].Red -gt $before[1].Blue * 3)) { throw 'Before image did not reproduce inverted video' }
if (-not ($after[0].Red -gt $after[0].Blue * 3 -and $after[1].Blue -gt $after[1].Red * 3)) { throw 'After image has incorrect orientation' }
$result = @{ Result = 'PASS'; Expected = 'Top red, bottom blue'; Before = $before; After = $after }
$result | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $saved 'orientation-color-check.json') -Encoding utf8
$result | ConvertTo-Json -Depth 5
