param(
    [string]$Model = "gpt-image-1",
    [string]$Quality = "medium",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SecretsPath = Join-Path $ProjectDir "config/secrets.local.json"
$StyleReference = Join-Path $ProjectDir "visuals/style/examples/approved-comic-panel-character-free.png"
$OutDir = Join-Path $ProjectDir "visuals/style/characters/expanded"
$Size = "1536x1024"

$Characters = @(
    @{
        Slug = "mara"
        Profile = "Black woman, late 20s, tall athletic build, deep brown skin, short natural curls. Outfit: rust cardigan, cream shirt, dark jeans, simple canvas sneakers. Warm, confident, easy smile."
    },
    @{
        Slug = "diego"
        Profile = "Latino man, early 30s, medium build, tan skin, short wavy dark hair, trimmed beard. Outfit: denim overshirt, pale green T-shirt, charcoal pants. Relaxed, friendly, expressive hands."
    },
    @{
        Slug = "aiko"
        Profile = "East Asian woman, mid 40s, average build, light-medium skin, neat shoulder-length black hair. Outfit: navy cardigan, white blouse, gray slacks, small stud earrings. Calm, precise, helpful."
    },
    @{
        Slug = "samir"
        Profile = "South Asian man, late 50s, average build, medium-brown skin, salt-and-pepper hair, mustache. Outfit: teal button-up shirt, charcoal vest, dark trousers. Patient, thoughtful, gentle authority."
    },
    @{
        Slug = "nadia"
        Profile = "Middle Eastern woman, early 30s, curvy build, olive skin, soft round face, patterned headscarf. Outfit: plum tunic, long beige cardigan, dark pants. Lively, welcoming, practical."
    },
    @{
        Slug = "liam"
        Profile = "White man, early 20s, slim build, fair skin, sandy blond hair, light freckles. Outfit: forest-green hoodie, white T-shirt, tan chinos. Cheerful, slightly awkward, earnest."
    },
    @{
        Slug = "sofia"
        Profile = "Older Latina woman, late 60s, short sturdy build, warm brown skin, silver curly bob. Outfit: cobalt blouse, patterned scarf, dark skirt, comfortable shoes. Kind, observant, reassuring."
    },
    @{
        Slug = "kwame"
        Profile = "Black man, early 40s, broad build, dark brown skin, shaved head. Outfit: light blue collared shirt, charcoal utility vest, navy trousers. Steady, attentive, protective."
    },
    @{
        Slug = "elena"
        Profile = "Eastern European woman, mid 30s, slim build, fair skin, straight auburn bob, rectangular glasses. Outfit: mustard sweater, white collared shirt, dark trousers. Focused, clear, politely direct."
    },
    @{
        Slug = "tariq"
        Profile = "North African teen boy, late teens, slender build, medium olive-brown skin, thick curly dark hair. Outfit: burgundy sweatshirt, black jeans, white sneakers, simple backpack strap. Energetic, curious, quick smile."
    }
)

function Read-JsonFile($Path) {
    $text = [System.IO.File]::ReadAllText((Resolve-Path $Path), [System.Text.Encoding]::UTF8)
    return $text | ConvertFrom-Json
}

function Relative-Path($Path) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    return $fullPath.Replace($ProjectDir + "\", "").Replace("\", "/")
}

function Add-StringPart($Stream, $Boundary, $Name, $Value) {
    $text = "--$Boundary`r`nContent-Disposition: form-data; name=`"$Name`"`r`n`r`n$Value`r`n"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
    $Stream.Write($bytes, 0, $bytes.Length)
}

function Add-FilePart($Stream, $Boundary, $Name, $Path) {
    $fileName = [System.IO.Path]::GetFileName($Path)
    $header = "--$Boundary`r`nContent-Disposition: form-data; name=`"$Name`"; filename=`"$fileName`"`r`nContent-Type: image/png`r`n`r`n"
    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
    $Stream.Write($headerBytes, 0, $headerBytes.Length)
    $fileBytes = [System.IO.File]::ReadAllBytes($Path)
    $Stream.Write($fileBytes, 0, $fileBytes.Length)
    $newline = [System.Text.Encoding]::UTF8.GetBytes("`r`n")
    $Stream.Write($newline, 0, $newline.Length)
}

function Invoke-ImageEdit($ApiKey, $Prompt, $OutPath, $ReferencePaths) {
    $boundary = "----AudioLanguageBoundary$([Guid]::NewGuid().ToString("N"))"
    $stream = New-Object System.IO.MemoryStream
    Add-StringPart $stream $boundary "model" $Model
    Add-StringPart $stream $boundary "prompt" $Prompt
    Add-StringPart $stream $boundary "n" "1"
    Add-StringPart $stream $boundary "size" $Size
    Add-StringPart $stream $boundary "quality" $Quality
    Add-StringPart $stream $boundary "output_format" "png"
    foreach ($reference in $ReferencePaths) {
        if (Test-Path -LiteralPath $reference) {
            Add-FilePart $stream $boundary "image[]" $reference
        }
    }
    $footer = [System.Text.Encoding]::UTF8.GetBytes("--$boundary--`r`n")
    $stream.Write($footer, 0, $footer.Length)
    $body = $stream.ToArray()
    $stream.Dispose()

    $headers = @{ Authorization = "Bearer $ApiKey" }
    $response = Invoke-RestMethod `
        -Uri "https://api.openai.com/v1/images/edits" `
        -Method Post `
        -Headers $headers `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body

    $b64 = $response.data[0].b64_json
    if (-not $b64) {
        throw "Image API returned no base64 PNG data for $OutPath"
    }
    [System.IO.File]::WriteAllBytes($OutPath, [Convert]::FromBase64String($b64))
}

function Build-Prompt($Character) {
    return @"
Create a reusable single-character reference sheet for a language-learning comic app.

Style: polished clean anime/comic illustration matching the attached character-free style reference: crisp controlled linework, warm flat colors, subtle cel shading, readable face and hands, ordinary human proportions, mobile-friendly clarity.

Character profile: $($Character.Profile)

Reference sheet layout: show exactly one character identity repeated in three views on a plain warm neutral background: front-facing neutral standing pose, three-quarter conversational pose, and a smaller expression/gesture variation. The repeated views must clearly be the same person with the same clothing, hairstyle, body type, age impression, skin tone, and accessories.

Use this character as a reusable scene partner, not tied to any single phrase or scenario. Make the person look ordinary, grounded, approachable, and suitable for everyday public dialogue scenes.

Constraints: no other people, no speech bubbles, no captions, no labels, no readable text, no logos, no UI, no name tags with writing, no decorative border, no photorealism, no mascot style, no exaggerated fantasy clothing.
"@
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$secrets = Read-JsonFile $SecretsPath
$apiKey = [string]$secrets.OPENAI_API_KEY
if (-not $apiKey) {
    throw "OPENAI_API_KEY missing from $SecretsPath"
}

$created = 0
$skipped = 0
foreach ($character in $Characters) {
    $outPath = Join-Path $OutDir ("{0}-reference.png" -f $character.Slug)
    $promptPath = Join-Path $OutDir ("{0}-reference.txt" -f $character.Slug)
    $prompt = Build-Prompt $character
    [System.IO.File]::WriteAllText($promptPath, $prompt, [System.Text.UTF8Encoding]::new($false))
    if ((Test-Path -LiteralPath $outPath) -and -not $Force) {
        Write-Host "skip $((Relative-Path $outPath))"
        $skipped += 1
        continue
    }
    Write-Host "generate $((Relative-Path $outPath))"
    Invoke-ImageEdit $apiKey $prompt $outPath @($StyleReference)
    $created += 1
}

Write-Host "created=$created skipped=$skipped model=$Model quality=$Quality"
