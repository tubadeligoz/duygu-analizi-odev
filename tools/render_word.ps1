param(
    [Parameter(Mandatory=$true)][string]$InputDocx,
    [Parameter(Mandatory=$true)][string]$OutputPdf
)
$ErrorActionPreference = 'Stop'
$inputPath = (Resolve-Path -LiteralPath $InputDocx).Path
$outputPath = [System.IO.Path]::GetFullPath($OutputPdf)
[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($outputPath)) | Out-Null
$word = $null
$document = $null
$existingCount = 0
try {
    $word = New-Object -ComObject Word.Application
    $existingCount = $word.Documents.Count
    $oldAlerts = $word.DisplayAlerts
    $oldSecurity = $word.AutomationSecurity
    if ($existingCount -eq 0) { $word.Visible = $false }
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $document = $word.Documents.Open($inputPath, $false, $true, $false)
    $document.Repaginate()
    $pages = $document.ComputeStatistics(2)
    $document.ExportAsFixedFormat($outputPath, 17)
    [pscustomobject]@{ Pages=$pages; Pdf=$outputPath; Renderer='Microsoft Word native PDF export' } | ConvertTo-Json
} finally {
    if ($null -ne $document) {
        $document.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
    }
    if ($null -ne $word) {
        $word.DisplayAlerts = $oldAlerts
        $word.AutomationSecurity = $oldSecurity
        if ($existingCount -eq 0) { $word.Quit(0) }
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($word)
    }
}
