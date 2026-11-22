param(
    [Parameter(Mandatory=$true)][string]$InputDocx,
    [Parameter(Mandatory=$true)][string]$OutputPdf,
    [string]$SubmissionDocx,
    [string]$SubmissionPdf
)
$ErrorActionPreference = 'Stop'
$jobs = @(@{ Input=$InputDocx; Output=$OutputPdf })
if ($SubmissionDocx) {
    if (-not $SubmissionPdf) { throw 'SubmissionPdf is required with SubmissionDocx' }
    $jobs += @{ Input=$SubmissionDocx; Output=$SubmissionPdf }
}
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
    foreach ($job in $jobs) {
        $inputPath = (Resolve-Path -LiteralPath $job.Input).Path
        $outputPath = [System.IO.Path]::GetFullPath($job.Output)
        [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($outputPath)) | Out-Null
        $document = $word.Documents.Open($inputPath, $false, $false, $false)
        [void]$document.Fields.Update()
        $document.Repaginate()
        foreach ($toc in $document.TablesOfContents) { $toc.Update() }
        $document.Repaginate()
        foreach ($toc in $document.TablesOfContents) { $toc.UpdatePageNumbers() }
        [void]$document.Fields.Update()
        $document.Repaginate()
        $document.Save()
        $pages = $document.ComputeStatistics(2)
        $words = $document.ComputeStatistics(0)
        $tocCount = $document.TablesOfContents.Count
        $document.ExportAsFixedFormat($outputPath, 17)
        [pscustomobject]@{ Pages=$pages; Words=$words; TablesOfContents=$tocCount; Pdf=$outputPath; Renderer='Microsoft Word native PDF export' } | ConvertTo-Json
        $document.Close(0)
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)
        $document = $null
    }
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
