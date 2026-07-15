[CmdletBinding()]
param(
    [string]$RepositoryPath = ""
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$script:failureCount = 0
$script:warningCount = 0

function Pass([string]$Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Fail([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $script:failureCount++
}

function Warn([string]$Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
    $script:warningCount++
}

function Get-LineNumber {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][int]$Index
    )

    if ($Index -le 0) {
        return 1
    }

    return [regex]::Matches($Content.Substring(0, $Index), "`n").Count + 1
}

function Get-AttributeValue {
    param(
        [Parameter(Mandatory = $true)][System.Text.RegularExpressions.Match]$Match
    )

    foreach ($groupName in @("double", "single", "bare")) {
        if ($Match.Groups[$groupName].Success) {
            return $Match.Groups[$groupName].Value
        }
    }

    return $null
}

function Test-IsLocalReference {
    param([AllowEmptyString()][string]$Reference)

    if ([string]::IsNullOrWhiteSpace($Reference)) {
        return $false
    }

    $candidate = [System.Net.WebUtility]::HtmlDecode($Reference).Trim()
    if ($candidate.StartsWith("<") -and $candidate.EndsWith(">")) {
        $candidate = $candidate.Substring(1, $candidate.Length - 2).Trim()
    }

    return $candidate -notmatch '^(?i)(?:[a-z][a-z0-9+.-]*:|//|#)'
}

function Get-MarkdownDestination {
    param([AllowEmptyString()][string]$Destination)

    $candidate = $Destination.Trim()
    if ($candidate.StartsWith("<")) {
        $closingBracket = $candidate.IndexOf(">")
        if ($closingBracket -gt 0) {
            return $candidate.Substring(1, $closingBracket - 1)
        }
    }

    return ($candidate -split '\s+', 2)[0]
}

function Get-GitHubHeadingSlug {
    param([AllowEmptyString()][string]$Heading)

    $plainText = [System.Net.WebUtility]::HtmlDecode($Heading)
    $plainText = [regex]::Replace($plainText, '!\[([^\]]*)\]\([^)]*\)', '$1')
    $plainText = [regex]::Replace($plainText, '\[([^\]]+)\]\([^)]*\)', '$1')
    $plainText = [regex]::Replace($plainText, '<[^>]+>', '')
    $plainText = $plainText.Replace('`', '').ToLowerInvariant()

    # GitHub keeps letters, marks, numbers, spaces, hyphens and underscores,
    # while punctuation and symbols (including heading emojis) are removed.
    $plainText = [regex]::Replace($plainText, '[^\p{L}\p{M}\p{N}\s_-]', '')
    return [regex]::Replace($plainText, '\s', '-')
}

function Test-ExactPathCase {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath,
        [Parameter(Mandatory = $true)][string]$FullPath
    )

    $normalizedRoot = [System.IO.Path]::GetFullPath($RootPath).TrimEnd('\', '/')
    $normalizedFullPath = [System.IO.Path]::GetFullPath($FullPath)
    if (-not $normalizedFullPath.StartsWith($normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $false
    }

    $relativePath = $normalizedFullPath.Substring($normalizedRoot.Length).TrimStart('\', '/')
    $currentPath = $normalizedRoot
    foreach ($segment in @($relativePath -split '[\\/]')) {
        if ([string]::IsNullOrWhiteSpace($segment)) {
            continue
        }

        $exactMatches = @(Get-ChildItem -LiteralPath $currentPath -Force | Where-Object { $_.Name -ceq $segment })
        if ($exactMatches.Count -ne 1) {
            return $false
        }

        $currentPath = $exactMatches[0].FullName
    }

    return $true
}

try {
    if ([string]::IsNullOrWhiteSpace($RepositoryPath)) {
        $RepositoryPath = Join-Path $PSScriptRoot "..\.."
    }

    $RepositoryPath = [System.IO.Path]::GetFullPath($RepositoryPath)
}
catch {
    Fail "Repository path could not be resolved: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "PROFILE VERIFICATION FAILED (1 failure, 0 warnings)" -ForegroundColor Red
    exit 1
}

$repositoryPrefix = ($RepositoryPath -replace '[\\/]+$', '') + [System.IO.Path]::DirectorySeparatorChar

if (Test-Path -LiteralPath (Join-Path $RepositoryPath ".git") -PathType Any) {
    Pass "Git repository metadata detected."
}
else {
    Fail ".git metadata is missing."
}

$readmePath = Join-Path $RepositoryPath "README.md"
$readme = $null
$tagMatches = @()
$uniqueLocalPaths = @{}

if (-not (Test-Path -LiteralPath $readmePath -PathType Leaf)) {
    Fail "README.md is missing."
}
else {
    try {
        $readme = Get-Content -LiteralPath $readmePath -Raw -Encoding UTF8
        $tagMatches = @([regex]::Matches($readme, '(?is)<(?<tag>[a-z][a-z0-9:-]*)\b(?<attributes>[^>]*)>'))
    }
    catch {
        Fail "README.md could not be read: $($_.Exception.Message)"
    }
}

if ($null -ne $readme) {
    if ($readme.Length -gt 100) {
        Pass "README.md contains profile content."
    }
    else {
        Fail "README.md is unexpectedly short."
    }

    foreach ($required in @("Kevin Cusnir", "Lirioth Teltanion", "kevincusnir@gmail.com")) {
        if ($readme.Contains($required)) {
            Pass "Required identity found: $required"
        }
        else {
            Fail "Required identity is missing: $required"
        }
    }

    if ($readme -match 'kevincusnir@(?:gmail\.)?dot\s+com') {
        Fail "A written 'dot com' email typo was detected."
    }

    # Validate alt text for HTML and Markdown images.
    $htmlImageCount = 0
    $markdownImageCount = 0
    $altFailureCountBefore = $script:failureCount
    $altPattern = '(?is)(?:^|\s)alt\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'
    $rolePattern = '(?is)(?:^|\s)role\s*=\s*(?:"presentation"|''presentation''|presentation)(?:\s|$)'
    $ariaHiddenPattern = '(?is)(?:^|\s)aria-hidden\s*=\s*(?:"true"|''true''|true)(?:\s|$)'

    foreach ($tagMatch in $tagMatches) {
        if ($tagMatch.Groups["tag"].Value -ine "img") {
            continue
        }

        $htmlImageCount++
        $attributes = $tagMatch.Groups["attributes"].Value
        $altMatch = [regex]::Match($attributes, $altPattern)
        $line = Get-LineNumber -Content $readme -Index $tagMatch.Index

        if (-not $altMatch.Success) {
            Fail "HTML image on README.md line $line is missing an alt attribute."
            continue
        }

        $altText = [System.Net.WebUtility]::HtmlDecode([string](Get-AttributeValue -Match $altMatch)).Trim()
        $isDecorative = [regex]::IsMatch($attributes, $rolePattern) -or [regex]::IsMatch($attributes, $ariaHiddenPattern)
        if ([string]::IsNullOrWhiteSpace($altText) -and -not $isDecorative) {
            Fail "HTML image on README.md line $line has empty alt text without decorative semantics."
        }
    }

    $markdownImageMatches = @([regex]::Matches($readme, '(?m)!\[(?<alt>[^\]\r\n]*)\]\((?<target>[^)\r\n]+)\)'))
    $markdownLinkMatches = @([regex]::Matches($readme, '(?m)(?<!\!)\[[^\]\r\n]+\]\((?<target>[^)\r\n]+)\)'))
    foreach ($imageMatch in $markdownImageMatches) {
        $markdownImageCount++
        if ([string]::IsNullOrWhiteSpace($imageMatch.Groups["alt"].Value)) {
            $line = Get-LineNumber -Content $readme -Index $imageMatch.Index
            Fail "Markdown image on README.md line $line has empty alt text."
        }
    }

    if ($script:failureCount -eq $altFailureCountBefore) {
        Pass "All $($htmlImageCount + $markdownImageCount) README images provide alt text or explicit decorative semantics."
    }

    # Collect local asset references from HTML src/srcset/href and Markdown links or images.
    $localReferences = New-Object System.Collections.ArrayList
    $srcAttributeCount = 0
    $srcsetAttributeCount = 0
    $localLinkTargetCount = 0
    $sourcePattern = '(?is)(?:^|\s)(?<attribute>src|srcset)\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'
    $hrefPattern = '(?is)(?:^|\s)href\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'

    foreach ($tagMatch in $tagMatches) {
        $attributes = $tagMatch.Groups["attributes"].Value
        $sourceMatches = @([regex]::Matches($attributes, $sourcePattern))
        foreach ($sourceMatch in $sourceMatches) {
            $attributeName = $sourceMatch.Groups["attribute"].Value.ToLowerInvariant()
            $attributeValue = Get-AttributeValue -Match $sourceMatch
            $absoluteIndex = $tagMatch.Groups["attributes"].Index + $sourceMatch.Index
            $line = Get-LineNumber -Content $readme -Index $absoluteIndex

            if ($attributeName -eq "srcset") {
                $srcsetAttributeCount++
                $candidates = @($attributeValue -split '\s*,\s*')
            }
            else {
                $srcAttributeCount++
                $candidates = @($attributeValue)
            }

            if ([string]::IsNullOrWhiteSpace($attributeValue)) {
                Fail "Empty $attributeName attribute on README.md line $line."
                continue
            }

            foreach ($candidateEntry in $candidates) {
                $candidate = ($candidateEntry.Trim() -split '\s+', 2)[0]
                if (Test-IsLocalReference -Reference $candidate) {
                    [void]$localReferences.Add([pscustomobject]@{
                        Reference = $candidate
                        Line      = $line
                        Source    = "HTML $attributeName"
                    })
                }
            }
        }
    }

    foreach ($tagMatch in $tagMatches) {
        $hrefMatches = @([regex]::Matches($tagMatch.Groups["attributes"].Value, $hrefPattern))
        foreach ($hrefMatch in $hrefMatches) {
            $candidate = Get-AttributeValue -Match $hrefMatch
            if (Test-IsLocalReference -Reference $candidate) {
                $localLinkTargetCount++
                [void]$localReferences.Add([pscustomobject]@{
                    Reference = $candidate
                    Line      = Get-LineNumber -Content $readme -Index $tagMatch.Index
                    Source    = "HTML href"
                })
            }
        }
    }

    foreach ($imageMatch in $markdownImageMatches) {
        $candidate = Get-MarkdownDestination -Destination $imageMatch.Groups["target"].Value
        if (Test-IsLocalReference -Reference $candidate) {
            [void]$localReferences.Add([pscustomobject]@{
                Reference = $candidate
                Line      = Get-LineNumber -Content $readme -Index $imageMatch.Index
                Source    = "Markdown image"
            })
        }
    }

    foreach ($linkMatch in $markdownLinkMatches) {
        $candidate = Get-MarkdownDestination -Destination $linkMatch.Groups["target"].Value
        if (Test-IsLocalReference -Reference $candidate) {
            $localLinkTargetCount++
            [void]$localReferences.Add([pscustomobject]@{
                Reference = $candidate
                Line      = Get-LineNumber -Content $readme -Index $linkMatch.Index
                Source    = "Markdown link"
            })
        }
    }

    $assetFailureCountBefore = $script:failureCount
    $uniqueLocalPaths = @{}
    foreach ($localReference in $localReferences) {
        $referencePath = [System.Net.WebUtility]::HtmlDecode([string]$localReference.Reference).Trim()
        if ($referencePath.StartsWith("<") -and $referencePath.EndsWith(">")) {
            $referencePath = $referencePath.Substring(1, $referencePath.Length - 2).Trim()
        }
        $referencePath = ($referencePath -split '[?#]', 2)[0]

        try {
            $referencePath = [System.Uri]::UnescapeDataString($referencePath)
        }
        catch {
            Fail "Malformed local asset reference '$($localReference.Reference)' on README.md line $($localReference.Line)."
            continue
        }

        if ([System.IO.Path]::IsPathRooted($referencePath)) {
            Fail "Local asset reference '$($localReference.Reference)' on README.md line $($localReference.Line) must be repository-relative."
            continue
        }

        try {
            $normalizedPath = $referencePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar).Replace('\', [System.IO.Path]::DirectorySeparatorChar)
            $fullPath = [System.IO.Path]::GetFullPath((Join-Path $RepositoryPath $normalizedPath))
        }
        catch {
            Fail "Local asset reference '$($localReference.Reference)' on README.md line $($localReference.Line) is invalid: $($_.Exception.Message)"
            continue
        }

        if (-not $fullPath.StartsWith($repositoryPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            Fail "Local asset reference '$($localReference.Reference)' on README.md line $($localReference.Line) escapes the repository."
            continue
        }

        $pathKey = $fullPath.ToLowerInvariant()
        if (-not $uniqueLocalPaths.ContainsKey($pathKey)) {
            $uniqueLocalPaths[$pathKey] = $localReference.Reference
        }

        if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
            Fail "Missing local asset '$($localReference.Reference)' referenced by $($localReference.Source) on README.md line $($localReference.Line)."
        }
        elseif (-not (Test-ExactPathCase -RootPath $RepositoryPath -FullPath $fullPath)) {
            Fail "Local asset '$($localReference.Reference)' on README.md line $($localReference.Line) does not match the repository path casing exactly."
        }
    }

    if ($localReferences.Count -eq 0) {
        Warn "No local README assets were detected in src, srcset, href or Markdown references."
    }
    elseif ($script:failureCount -eq $assetFailureCountBefore) {
        Pass "All $($uniqueLocalPaths.Count) unique local README assets exist ($srcAttributeCount src, $srcsetAttributeCount srcset and $localLinkTargetCount local link targets inspected)."
    }

    # Every animated local SVG or GIF shown in README must provide reduced motion.
    $reducedMotionFailureCountBefore = $script:failureCount
    $animatedImageCount = 0
    $pictureMatches = @([regex]::Matches($readme, '(?is)<picture\b[^>]*>.*?</picture>'))
    $srcOnlyPattern = '(?is)(?:^|\s)src\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'
    $srcsetOnlyPattern = '(?is)(?:^|\s)srcset\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'
    $mediaPattern = '(?is)(?:^|\s)media\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'

    foreach ($tagMatch in $tagMatches) {
        if ($tagMatch.Groups["tag"].Value -ine "img") {
            continue
        }

        $srcMatch = [regex]::Match($tagMatch.Groups["attributes"].Value, $srcOnlyPattern)
        if (-not $srcMatch.Success) {
            continue
        }

        $srcValue = [System.Net.WebUtility]::HtmlDecode([string](Get-AttributeValue -Match $srcMatch)).Trim()
        if (-not (Test-IsLocalReference -Reference $srcValue)) {
            continue
        }

        $imageReferencePath = ($srcValue -split '[?#]', 2)[0]
        try {
            $imageReferencePath = [System.Uri]::UnescapeDataString($imageReferencePath)
            $normalizedImagePath = $imageReferencePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar).Replace('\', [System.IO.Path]::DirectorySeparatorChar)
            $fullImagePath = [System.IO.Path]::GetFullPath((Join-Path $RepositoryPath $normalizedImagePath))
        }
        catch {
            # The local-reference validation above already reports malformed paths.
            continue
        }

        if (-not $fullImagePath.StartsWith($repositoryPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            -not (Test-Path -LiteralPath $fullImagePath -PathType Leaf)) {
            continue
        }

        $extension = [System.IO.Path]::GetExtension($fullImagePath).ToLowerInvariant()
        $isAnimated = $extension -eq ".gif"
        $hasInternalReducedMotion = $false
        if ($extension -eq ".svg") {
            try {
                $svgContent = Get-Content -LiteralPath $fullImagePath -Raw -Encoding UTF8
                $hasSmilAnimation = $svgContent -match '(?is)<animate(?:Motion|Transform)?\b'
                $hasCssAnimation = $svgContent -match '(?is)@keyframes\b' -and $svgContent -match '(?is)animation\s*:'
                $isAnimated = $hasSmilAnimation -or $hasCssAnimation
                $hasInternalReducedMotion = (
                    $svgContent -match '(?is)@media\s*\([^)]*prefers-reduced-motion\s*:\s*reduce[^)]*\)' -and
                    $svgContent -match '(?is)animation\s*:\s*none\s*!important'
                )
            }
            catch {
                # SVG parsing below reports unreadable assets.
                continue
            }
        }

        if (-not $isAnimated) {
            continue
        }

        $animatedImageCount++
        $containingPicture = $null
        foreach ($pictureMatch in $pictureMatches) {
            if ($pictureMatch.Index -le $tagMatch.Index -and
                ($pictureMatch.Index + $pictureMatch.Length) -ge ($tagMatch.Index + $tagMatch.Length)) {
                $containingPicture = $pictureMatch
                break
            }
        }

        $hasReducedMotionSource = $false
        if ($null -ne $containingPicture) {
            $sourceTags = @([regex]::Matches($containingPicture.Value, '(?is)<source\b(?<attributes>[^>]*)>'))
            foreach ($sourceTag in $sourceTags) {
                $sourceAttributes = $sourceTag.Groups["attributes"].Value
                $mediaMatch = [regex]::Match($sourceAttributes, $mediaPattern)
                $srcsetMatch = [regex]::Match($sourceAttributes, $srcsetOnlyPattern)
                if (-not $mediaMatch.Success -or -not $srcsetMatch.Success) {
                    continue
                }

                $mediaValue = [System.Net.WebUtility]::HtmlDecode([string](Get-AttributeValue -Match $mediaMatch)).Trim()
                $srcsetValue = [System.Net.WebUtility]::HtmlDecode([string](Get-AttributeValue -Match $srcsetMatch)).Trim()
                if ($mediaValue -match '^\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*$' -and
                    -not [string]::IsNullOrWhiteSpace($srcsetValue)) {
                    $hasReducedMotionSource = $true
                    break
                }
            }
        }

        if (-not $hasReducedMotionSource -and -not $hasInternalReducedMotion) {
            $line = Get-LineNumber -Content $readme -Index $tagMatch.Index
            Fail "Animated image '$srcValue' on README.md line $line requires a reduced-motion <picture> source or an internal prefers-reduced-motion rule."
        }
    }

    if ($animatedImageCount -eq 0) {
        Warn "No animated local SVG or GIF images were detected in README.md."
    }
    elseif ($script:failureCount -eq $reducedMotionFailureCountBefore) {
        Pass "All $animatedImageCount animated local SVG or GIF images provide reduced-motion fallbacks."
    }

    # Register explicit HTML anchors and GitHub-style Markdown heading anchors.
    $anchorFailureCountBefore = $script:failureCount
    $explicitAnchors = @{}
    $allAnchors = @{}
    $explicitAnchorCount = 0
    $idPattern = '(?is)(?:^|\s)id\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'
    $namePattern = '(?is)(?:^|\s)name\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))'

    foreach ($tagMatch in $tagMatches) {
        $attributes = $tagMatch.Groups["attributes"].Value
        $anchorAttributeMatches = @([regex]::Matches($attributes, $idPattern))
        if ($tagMatch.Groups["tag"].Value -ieq "a") {
            $anchorAttributeMatches += @([regex]::Matches($attributes, $namePattern))
        }

        foreach ($anchorMatch in $anchorAttributeMatches) {
            $anchor = [System.Net.WebUtility]::HtmlDecode([string](Get-AttributeValue -Match $anchorMatch)).Trim()
            $line = Get-LineNumber -Content $readme -Index $tagMatch.Index
            if ([string]::IsNullOrWhiteSpace($anchor)) {
                Fail "Empty HTML anchor on README.md line $line."
                continue
            }

            $explicitAnchorCount++
            if ($explicitAnchors.ContainsKey($anchor)) {
                Fail "Duplicate HTML anchor '#$anchor' on README.md lines $($explicitAnchors[$anchor]) and $line."
            }
            else {
                $explicitAnchors[$anchor] = $line
                $allAnchors[$anchor] = $line
            }
        }
    }

    $headingAnchors = @{}
    $headingAnchorCount = 0
    $inFence = $false
    $readmeLines = @($readme -split "`r?`n")
    for ($lineIndex = 0; $lineIndex -lt $readmeLines.Count; $lineIndex++) {
        $lineText = $readmeLines[$lineIndex]
        if ($lineText -match '^\s*(?:`{3,}|~{3,})') {
            $inFence = -not $inFence
            continue
        }
        if ($inFence -or $lineText -notmatch '^\s{0,3}#{1,6}[\t ]+(?<heading>.+)$') {
            continue
        }

        $headingText = $Matches["heading"] -replace '\s+#+\s*$', ''
        $baseSlug = Get-GitHubHeadingSlug -Heading $headingText
        if ([string]::IsNullOrWhiteSpace($baseSlug)) {
            Warn "Markdown heading on README.md line $($lineIndex + 1) does not produce a linkable anchor."
            continue
        }

        $headingSlug = $baseSlug
        $suffix = 0
        while ($headingAnchors.ContainsKey($headingSlug)) {
            $suffix++
            $headingSlug = "$baseSlug-$suffix"
        }
        $headingAnchors[$headingSlug] = $lineIndex + 1
        $headingAnchorCount++

        if ($allAnchors.ContainsKey($headingSlug)) {
            Fail "Duplicate anchor '#$headingSlug' is produced by README.md lines $($allAnchors[$headingSlug]) and $($lineIndex + 1)."
        }
        else {
            $allAnchors[$headingSlug] = $lineIndex + 1
        }
    }

    # Verify that every internal fragment link points to a known explicit or heading anchor.
    $internalLinks = New-Object System.Collections.ArrayList
    foreach ($tagMatch in $tagMatches) {
        $hrefMatches = @([regex]::Matches($tagMatch.Groups["attributes"].Value, $hrefPattern))
        foreach ($hrefMatch in $hrefMatches) {
            $href = [System.Net.WebUtility]::HtmlDecode([string](Get-AttributeValue -Match $hrefMatch)).Trim()
            if ($href.StartsWith("#")) {
                [void]$internalLinks.Add([pscustomobject]@{
                    Target = $href
                    Line   = Get-LineNumber -Content $readme -Index $tagMatch.Index
                })
            }
        }
    }

    foreach ($linkMatch in $markdownLinkMatches) {
        $target = Get-MarkdownDestination -Destination $linkMatch.Groups["target"].Value
        if ($target.StartsWith("#")) {
            [void]$internalLinks.Add([pscustomobject]@{
                Target = $target
                Line   = Get-LineNumber -Content $readme -Index $linkMatch.Index
            })
        }
    }

    $missingAnchorCount = 0
    foreach ($internalLink in $internalLinks) {
        $fragment = [System.Net.WebUtility]::HtmlDecode([string]$internalLink.Target).Substring(1)
        try {
            $fragment = [System.Uri]::UnescapeDataString($fragment)
        }
        catch {
            Fail "Malformed internal anchor link '$($internalLink.Target)' on README.md line $($internalLink.Line)."
            $missingAnchorCount++
            continue
        }

        if ([string]::IsNullOrWhiteSpace($fragment) -or -not $allAnchors.ContainsKey($fragment)) {
            Fail "Internal link '$($internalLink.Target)' on README.md line $($internalLink.Line) has no matching anchor."
            $missingAnchorCount++
        }
    }

    if ($script:failureCount -eq $anchorFailureCountBefore) {
        Pass "Anchors are valid: $explicitAnchorCount explicit, $headingAnchorCount generated and $($internalLinks.Count) internal links checked."
    }
}

# Parse every SVG asset with DTD processing disabled.
$svgFailureCountBefore = $script:failureCount
try {
    $assetsPath = Join-Path $RepositoryPath "assets"
    $svgFiles = @()
    if (Test-Path -LiteralPath $assetsPath -PathType Container) {
        $svgFiles = @(Get-ChildItem -LiteralPath $assetsPath -Recurse -File -Filter "*.svg")
    }

    if ($svgFiles.Count -eq 0) {
        Warn "No SVG assets were found under assets/."
    }
    else {
        foreach ($svgFile in $svgFiles) {
            $reader = $null
            try {
                $settings = New-Object System.Xml.XmlReaderSettings
                $settings.DtdProcessing = [System.Xml.DtdProcessing]::Prohibit
                $settings.XmlResolver = $null
                $reader = [System.Xml.XmlReader]::Create($svgFile.FullName, $settings)

                $document = New-Object System.Xml.XmlDocument
                $document.XmlResolver = $null
                $document.Load($reader)

                if ($null -eq $document.DocumentElement -or $document.DocumentElement.LocalName -ine "svg") {
                    $relativeSvgPath = $svgFile.FullName.Substring($repositoryPrefix.Length).Replace('\', '/')
                    Fail "SVG asset '$relativeSvgPath' does not have an <svg> root element."
                }
                else {
                    $relativeSvgPath = $svgFile.FullName.Substring($repositoryPrefix.Length).Replace('\', '/')
                    $pathKey = $svgFile.FullName.ToLowerInvariant()
                    if ($uniqueLocalPaths.ContainsKey($pathKey)) {
                        $root = $document.DocumentElement
                        $titleNode = $root.SelectSingleNode("./*[local-name()='title']")
                        $descNode = $root.SelectSingleNode("./*[local-name()='desc']")
                        $ariaLabelledBy = $root.GetAttribute("aria-labelledby")
                        if ($root.GetAttribute("role") -ine "img" -or
                            $null -eq $titleNode -or
                            $null -eq $descNode -or
                            [string]::IsNullOrWhiteSpace($ariaLabelledBy)) {
                            Fail "Referenced SVG asset '$relativeSvgPath' requires role='img', aria-labelledby, <title> and <desc>."
                        }
                    }

                    # CSS transform animations override SVG placement transforms in browsers.
                    # Animated classes must live on a nested element, not on the positioned element.
                    $svgContent = Get-Content -LiteralPath $svgFile.FullName -Raw -Encoding UTF8
                    $animatedClasses = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::Ordinal)
                    $styleBlocks = @([regex]::Matches($svgContent, '(?is)(?<selector>[^{}]+)\{(?<body>[^{}]*animation\s*:[^{}]*)\}'))
                    foreach ($styleBlock in $styleBlocks) {
                        foreach ($classMatch in @([regex]::Matches($styleBlock.Groups["selector"].Value, '\.(?<name>[A-Za-z_][A-Za-z0-9_-]*)'))) {
                            [void]$animatedClasses.Add($classMatch.Groups["name"].Value)
                        }
                    }

                    if ($animatedClasses.Count -gt 0) {
                        $elementMatches = @([regex]::Matches($svgContent, '(?is)<[A-Za-z][A-Za-z0-9:-]*\b(?<attributes>[^>]*)>'))
                        foreach ($elementMatch in $elementMatches) {
                            $attributes = $elementMatch.Groups["attributes"].Value
                            if ($attributes -notmatch '(?is)(?:^|\s)transform\s*=') {
                                continue
                            }

                            $classAttribute = [regex]::Match($attributes, '(?is)(?:^|\s)class\s*=\s*(?:"(?<double>[^"]*)"|''(?<single>[^'']*)''|(?<bare>[^\s>]+))')
                            if (-not $classAttribute.Success) {
                                continue
                            }

                            $classValue = [string](Get-AttributeValue -Match $classAttribute)
                            foreach ($className in @($classValue -split '\s+')) {
                                if ($animatedClasses.Contains($className)) {
                                    Fail "SVG asset '$relativeSvgPath' applies animated class '$className' to an element with a placement transform; use a nested animation wrapper."
                                    break
                                }
                            }
                        }
                    }
                }
            }
            catch {
                $relativeSvgPath = $svgFile.FullName
                if ($svgFile.FullName.StartsWith($repositoryPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $relativeSvgPath = $svgFile.FullName.Substring($repositoryPrefix.Length).Replace('\', '/')
                }
                Fail "SVG asset '$relativeSvgPath' is not valid XML: $($_.Exception.Message)"
            }
            finally {
                if ($null -ne $reader) {
                    $reader.Dispose()
                }
            }
        }

        if ($script:failureCount -eq $svgFailureCountBefore) {
            Pass "All $($svgFiles.Count) SVG assets are well-formed XML with an <svg> root element."
        }
    }
}
catch {
    Fail "SVG validation could not be completed: $($_.Exception.Message)"
}

# Decode referenced raster images and enforce a lightweight public-profile payload budget.
$rasterFailureCountBefore = $script:failureCount
try {
    Add-Type -AssemblyName System.Drawing
    $referencedVisualBytes = [int64]0
    $referencedVisualCount = 0
    $decodedRasterCount = 0
    foreach ($fullPathKey in @($uniqueLocalPaths.Keys)) {
        $extension = [System.IO.Path]::GetExtension($fullPathKey).ToLowerInvariant()
        if ($extension -notin @(".svg", ".png", ".gif")) {
            continue
        }

        if (-not (Test-Path -LiteralPath $fullPathKey -PathType Leaf)) {
            continue
        }

        $fileInfo = Get-Item -LiteralPath $fullPathKey
        $referencedVisualBytes += $fileInfo.Length
        $referencedVisualCount++

        $perFileLimit = if ($extension -eq ".gif") { 5MB } elseif ($extension -eq ".png") { 2MB } else { 512KB }
        if ($fileInfo.Length -gt $perFileLimit) {
            $relativePath = $fileInfo.FullName.Substring($repositoryPrefix.Length).Replace('\', '/')
            Fail "Referenced visual '$relativePath' is $([math]::Round($fileInfo.Length / 1MB, 2)) MiB; limit is $([math]::Round($perFileLimit / 1MB, 2)) MiB."
        }

        if ($extension -notin @(".png", ".gif")) {
            continue
        }

        $image = $null
        try {
            $image = [System.Drawing.Image]::FromFile($fileInfo.FullName)
            if ($image.Width -le 0 -or $image.Height -le 0) {
                throw "Image dimensions are invalid."
            }
            $decodedRasterCount++
        }
        catch {
            $relativePath = $fileInfo.FullName.Substring($repositoryPrefix.Length).Replace('\', '/')
            Fail "Referenced raster '$relativePath' could not be decoded: $($_.Exception.Message)"
        }
        finally {
            if ($null -ne $image) {
                $image.Dispose()
            }
        }
    }

    if ($referencedVisualBytes -gt 8MB) {
        Fail "Referenced local visuals total $([math]::Round($referencedVisualBytes / 1MB, 2)) MiB; public-profile budget is 8 MiB."
    }
    elseif ($script:failureCount -eq $rasterFailureCountBefore) {
        Pass "Referenced visual payload is $([math]::Round($referencedVisualBytes / 1MB, 2)) MiB across $referencedVisualCount files; $decodedRasterCount raster images decoded."
    }
}
catch {
    Fail "Raster and payload validation could not be completed: $($_.Exception.Message)"
}

if (Test-Path -LiteralPath (Join-Path $RepositoryPath "AGENTS.md") -PathType Leaf) {
    Pass "AGENTS.md is available to Codex."
}
else {
    Fail "AGENTS.md is missing."
}

Write-Host ""
if ($script:failureCount -gt 0) {
    Write-Host "PROFILE VERIFICATION FAILED ($($script:failureCount) failure(s), $($script:warningCount) warning(s))" -ForegroundColor Red
    exit 1
}

Write-Host "PROFILE VERIFICATION PASSED (0 failures, $($script:warningCount) warning(s))" -ForegroundColor Green
exit 0
