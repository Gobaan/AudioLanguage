param(
    [int]$Limit = 0,
    [string]$OnlyDialogue = "",
    [int]$OnlyFrame = -1,
    [string]$Model = "gpt-image-1-mini",
    [string]$Quality = "low",
    [string]$OutputRoot = "visuals/Drafts",
    [switch]$Force,
    [switch]$PromptOnly
)

$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ResolvedOutputRoot = if ([System.IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot
} else {
    Join-Path $ProjectDir $OutputRoot
}
$SecretsPath = Join-Path $ProjectDir "project_config/config/secrets.local.json"
$DataPath = Join-Path $ProjectDir "data/languages/ja/dialogues.json"
$PromptsPath = Join-Path $ProjectDir "data/languages/ja/visual_prompts.json"
$StyleReference = Join-Path $ProjectDir "visuals/style/examples/approved-comic-panel-character-free.png"
$CharacterDir = Join-Path $ProjectDir "visuals/style/characters"
$ExpandedCharacterDir = Join-Path $CharacterDir "expanded"
$Size = "1536x1024"

$PartnerReferenceByRole = @{
    barista = "vendor-reference.png"
    cashier = "vendor-reference.png"
    class_partner = "friend-reference.png"
    classmate = "friend-reference.png"
    friend = "friend-reference.png"
    host = "staff-reference.png"
    local = "local-helper-reference.png"
    laundry_attendant = "staff-reference.png"
    neighbor = "friend-reference.png"
    receptionist = "staff-reference.png"
    server = "vendor-reference.png"
    staff = "staff-reference.png"
    station_helper = "staff-reference.png"
    vendor = "vendor-reference.png"
}

$FullRegenerationDialogues = @(
    "ja-first-hi-response",
    "ja-introduce-self",
    "ja-repair-dont-understand",
    "ja-excuse-me-attention",
    "ja-order-local-food",
    "ja-directions-hospital",
    "ja-greeting-neighbor-transfer",
    "ja-greeting-entry-review",
    "ja-introduce-class-transfer",
    "ja-introduce-community-review",
    "ja-repair-ticket-transfer",
    "ja-repair-clinic-review",
    "ja-excuse-me-station-review",
    "ja-order-convenience-transfer",
    "ja-order-bakery-review",
    "ja-im-sorry-small-mistake",
    "ja-im-sorry-cafe-transfer",
    "ja-im-sorry-classroom-review",
    "ja-excuse-me-cafe-transfer"
)

$ScenePartnerByDialogue = @{
    "ja-directions-hospital" = @{ File = "kwame-reference.png" }
    "ja-excuse-me-attention" = @{ File = "sofia-reference.png" }
    "ja-excuse-me-cafe-transfer" = @{ File = "diego-reference.png" }
    "ja-excuse-me-station-review" = @{ File = "elena-reference.png" }
    "ja-first-hi-response" = @{ File = "liam-reference.png" }
    "ja-greeting-entry-review" = @{ File = "mara-reference.png" }
    "ja-greeting-neighbor-transfer" = @{ File = "sofia-reference.png" }
    "ja-im-sorry-cafe-transfer" = @{ File = "elena-reference.png" }
    "ja-im-sorry-classroom-review" = @{ File = "liam-reference.png" }
    "ja-im-sorry-small-mistake" = @{ File = "tariq-reference.png" }
    "ja-introduce-class-transfer" = @{ File = "tariq-reference.png" }
    "ja-introduce-community-review" = @{ File = "nadia-reference.png" }
    "ja-introduce-self" = @{ File = "aiko-reference.png" }
    "ja-order-bakery-review" = @{ File = "nadia-reference.png" }
    "ja-order-convenience-transfer" = @{ File = "aiko-reference.png" }
    "ja-order-local-food" = @{ File = "samir-reference.png" }
    "ja-repair-clinic-review" = @{ File = "samir-reference.png" }
    "ja-repair-dont-understand" = @{ File = "elena-reference.png" }
    "ja-repair-ticket-transfer" = @{ File = "kwame-reference.png" }
}

$SingleFrameFixes = @(
    @{ DialogueId = "ja-excuse-me-cafe-transfer"; OutputFrame = 3; SourceLine = 2; Note = "Keep the barista/cafe worker gender and identity consistent with the earlier frames." }
)

function Read-JsonFile($Path) {
    $text = [System.IO.File]::ReadAllText((Resolve-Path $Path), [System.Text.Encoding]::UTF8)
    return $text | ConvertFrom-Json
}

function Relative-Path($Path) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    return $fullPath.Replace($ProjectDir + "\", "").Replace("\", "/")
}

function Find-PartnerReference($Dialogue, $Line) {
    $dialogueReference = Find-ScenePartnerReference $Dialogue
    if ($dialogueReference) {
        return $dialogueReference
    }
    $speaker = [string]$Line.speaker_role
    if ($speaker -eq "learner") {
        foreach ($lineItem in $Dialogue.lines) {
            $role = [string]$lineItem.speaker_role
            if ($role -and $role -ne "learner" -and $PartnerReferenceByRole.ContainsKey($role)) {
                return Join-Path $CharacterDir $PartnerReferenceByRole[$role]
            }
        }
        return Join-Path $CharacterDir "staff-reference.png"
    }
    if ($PartnerReferenceByRole.ContainsKey($speaker)) {
        return Join-Path $CharacterDir $PartnerReferenceByRole[$speaker]
    }
    return Join-Path $CharacterDir "staff-reference.png"
}

function Find-ScenePartnerReference($Dialogue) {
    $dialogueId = [string]$Dialogue.id
    if ($ScenePartnerByDialogue.ContainsKey($dialogueId)) {
        return Join-Path $ExpandedCharacterDir $ScenePartnerByDialogue[$dialogueId].File
    }
    return $null
}

function Get-ScenePartnerIdentity($Dialogue, [string]$FallbackRole) {
    return Get-VisualRoleDescription $Dialogue $FallbackRole
}

function Allows-QuestionMarks($Dialogue, [int]$OutputFrame) {
    if ($OutputFrame -ne 2) {
        return $false
    }
    return @(
        "ja-repair-clinic-review",
        "ja-repair-dont-understand",
        "ja-repair-ticket-transfer"
    ) -contains [string]$Dialogue.id
}

function Find-ScenePartnerRole($Dialogue) {
    if ([string]$Dialogue.id -eq "ja-repair-clinic-review") {
        return "laundry_attendant"
    }
    if ([string]$Dialogue.id -eq "ja-excuse-me-attention") {
        return "passerby"
    }
    foreach ($lineItem in $Dialogue.lines) {
        $role = [string]$lineItem.speaker_role
        if ($role -and $role -ne "learner") {
            return $role
        }
    }
    return "scene partner"
}

function Find-PartnerReferenceByRole([string]$Role) {
    if ($Role -eq "passerby") {
        return Join-Path $ExpandedCharacterDir "sofia-reference.png"
    }
    if ($PartnerReferenceByRole.ContainsKey($Role)) {
        return Join-Path $CharacterDir $PartnerReferenceByRole[$Role]
    }
    return Join-Path $CharacterDir "staff-reference.png"
}

function Get-PromptItem($PromptManifest, $DialogueId, $LineIndex) {
    foreach ($item in $PromptManifest.prompts) {
        if ($item.dialogue_id -eq $DialogueId -and [int]$item.line_index -eq $LineIndex) {
            return $item
        }
    }
    throw "Missing prompt item for $DialogueId line $LineIndex"
}

function Build-BasePrompt($PromptItem, $Dialogue) {
    $localizedPrompt = Remove-FrameZeroBubbleLanguage (Get-LocalizedPromptForDraft $PromptItem)
    $partnerRole = Find-ScenePartnerRole $Dialogue
    $partnerReferenceName = [System.IO.Path]::GetFileName((Find-ScenePartnerReference $Dialogue))
    if (-not $partnerReferenceName) {
        $partnerReferenceName = [System.IO.Path]::GetFileName((Find-PartnerReferenceByRole $partnerRole))
    }
    $partnerIdentity = Get-ScenePartnerIdentity $Dialogue $partnerRole
    return @"
$localizedPrompt

OVERRIDE FOR NEW DRAFT WORKFLOW:
Create frame 0, the clean base setting for this dialogue scene.
This is not a spoken dialogue beat.
Leave the composition clear for the app UI: no captions, signs, labels, subtitles, or readable text anywhere.
Establish the stable room/location geometry, camera angle, character identities, character scale, lighting, and prop layout for the whole scene.
Both characters should be visible in a natural pre-dialogue or just-before-speaking moment. Keep the learner as the recurring female learner from learner-reference.png. Keep the scene partner exactly as $partnerIdentity controlled by $partnerReferenceName in all later frames.
"@
}

function Remove-FrameZeroBubbleLanguage([string]$Prompt) {
    $clean = Remove-PromptNoise $Prompt
    $clean = $clean -replace '(?m)^Do not draw speech bubbles\. The app will overlay the .* turn bubble\.\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^Mobile-safe composition: keep active characters, faces, hands, speech bubbles, and meaning cues', 'Mobile-safe composition: keep active characters, faces, hands, and key action'
    return $clean.Trim()
}

function Build-SpokenPrompt($PromptItem, $Dialogue, $Line, [int]$OutputFrame, [string]$ExtraNote = "") {
    $localizedPrompt = Remove-SpokenBubbleConflictLanguage (Get-LocalizedPromptForDraft $PromptItem)
    $speaker = [string]$Line.speaker_role
    if ([string]$Dialogue.id -eq "ja-repair-clinic-review" -and $speaker -eq "receptionist") {
        $speaker = "laundry_attendant"
    }
    if ([string]$Dialogue.id -eq "ja-excuse-me-cafe-transfer" -and $OutputFrame -eq 1) {
        return Build-SilentCafeFrameOnePrompt $localizedPrompt $Dialogue
    }
    $partnerRole = Find-ScenePartnerRole $Dialogue
    $partnerReferencePath = Find-ScenePartnerReference $Dialogue
    if (-not $partnerReferencePath) {
        $partnerReferencePath = Find-PartnerReferenceByRole $partnerRole
    }
    $partnerReferenceName = [System.IO.Path]::GetFileName($partnerReferencePath)
    $partnerIdentity = Get-ScenePartnerIdentity $Dialogue $partnerRole
    $otherRoles = @($Dialogue.lines | ForEach-Object { [string]$_.speaker_role } | Where-Object { $_ -and $_ -ne $speaker } | Select-Object -Unique)
    $other = if ($otherRoles.Count -gt 0) { $otherRoles[0] } else { "the other character" }
    $speakerDescription = Get-VisualRoleDescription $Dialogue $speaker
    $otherDescription = Get-VisualRoleDescription $Dialogue $other
    $placementNote = Get-SpecialFrameInstruction $Dialogue $OutputFrame
    $anchorFrame = Get-ContinuityAnchorFrame $Dialogue $OutputFrame
    $textRule = if (Allows-QuestionMarks $Dialogue $OutputFrame) {
        "Do not add captions, signs, labels, subtitles, translations, dialogue marks, or readable words. Exception: add only two or three small floating question marks near the learner to show confusion."
    } else {
        "Do not add captions, signs, labels, subtitles, translations, punctuation symbols, dialogue marks, or any readable text."
    }
    $referenceLine = if ($OutputFrame -gt 1) {
        "Create frame $OutputFrame as a dialogue action beat using the character references and accepted frame $anchorFrame continuity anchor."
    } else {
        "Create frame $OutputFrame as a dialogue action beat using the approved character-free style reference and character references."
    }
    $anchorLine = if ($OutputFrame -gt 1) {
        "Use the accepted frame $anchorFrame as the continuity anchor. Preserve its setting, camera angle, character identities, character scale, lighting, and prop layout while changing only the action beat for frame $OutputFrame."
    } else {
        "Establish the scene anchor for this dialogue: setting, camera angle, character identities, character scale, lighting, and prop layout."
    }
    return @"
$localizedPrompt

OVERRIDE FOR NEW DRAFT WORKFLOW:
$referenceLine
Show the body language, gaze, and scene action for this speaker turn.
$anchorLine
Stage the characters with clear readable separation: no overlapping faces, heads, torsos, or hands, and leave visible space between people unless the action explicitly requires a handoff.
Create one single continuous scene in one location. Do not create split-screen panels, multiple vignettes, before/after layouts, or separate scenes inside the same image.
$textRule
For frame 1, if the learner is not the active speaker, keep the learner listening or observing with hands relaxed and down. Do not show the learner waving, raising a hand, pointing, or already responding unless the prompt explicitly says the learner is acting first.

Character continuity:
- The learner is the recurring female learner controlled by learner-reference.png.
- The scene partner is exactly $partnerIdentity controlled by $partnerReferenceName.
- Preserve clothing family, hairstyle, body type, and age impression across the scene.

$placementNote
$ExtraNote
"@
}

function Get-ContinuityAnchorFrame($Dialogue, [int]$OutputFrame) {
    if ([string]$Dialogue.id -eq "ja-im-sorry-small-mistake" -and $OutputFrame -eq 3) {
        return 2
    }
    return 1
}

function Build-SilentCafeFrameOnePrompt([string]$LocalizedPrompt, $Dialogue) {
    $partnerReferencePath = Find-ScenePartnerReference $Dialogue
    if (-not $partnerReferencePath) {
        $partnerReferencePath = Join-Path $CharacterDir "vendor-reference.png"
    }
    $partnerReferenceName = [System.IO.Path]::GetFileName($partnerReferencePath)
    $partnerIdentity = Get-ScenePartnerIdentity $Dialogue "waiter / barista"
    return @"
$LocalizedPrompt

OVERRIDE FOR NEW DRAFT WORKFLOW:
Create frame 1 as a silent action beat using the approved character-free style reference and character references.
The waiter / barista is not speaking in this frame.
Keep the image free of captions, labels, subtitles, readable text, punctuation symbols, and dialogue marks.
Establish the scene anchor for this dialogue: setting, camera angle, character identities, character scale, lighting, and prop layout.
Stage the characters with clear readable separation: no overlapping faces, heads, torsos, or hands, and leave visible space between people.
Create one single continuous scene in one location. Do not create split-screen panels, multiple vignettes, before/after layouts, or separate scenes inside the same image.

Action requirement:
- The waiter / barista is walking away from the learner toward another table with other guests.
- The waiter / barista carries a tray and looks toward the other table, not at the learner.
- The waiter / barista faces away from the learner and does not look at the learner.
- The learner remains seated at her cafe table, noticing the waiter and preparing to get attention, with both hands relaxed and down near the table. The learner has not raised a hand yet.

Character continuity:
- The learner is the recurring female learner controlled by learner-reference.png.
- The scene partner is exactly $partnerIdentity controlled by $partnerReferenceName.
- Preserve clothing family, hairstyle, body type, and age impression across the scene.
"@
}

function Get-SpecialFrameInstruction($Dialogue, [int]$OutputFrame) {
    if ($OutputFrame -eq 1 -and @(
        "ja-excuse-me-station-review",
        "ja-greeting-entry-review",
        "ja-greeting-neighbor-transfer"
    ) -contains [string]$Dialogue.id) {
        return "Frame 1 is the partner/opening beat. The learner is not responding yet: keep the learner's hands relaxed and down, no raised hand, no wave, no pointing, no greeting gesture."
    }
    if ([string]$Dialogue.id -eq "ja-repair-clinic-review" -and $OutputFrame -eq 1) {
        return "Pull the washing machine close to the front foreground so its control panel is clearly visible. Both the learner and the laundry attendant point toward the same machine setting/control area. The machine must be a major visible object, not distant background."
    }
    if ([string]$Dialogue.id -eq "ja-repair-clinic-review" -and $OutputFrame -eq 2) {
        return "Show the learner clearly confused beside the washing machine controls: puzzled face, furrowed brow, looking between the control panel and attendant. Add two or three small floating question marks near the learner."
    }
    if ([string]$Dialogue.id -eq "ja-repair-dont-understand" -and $OutputFrame -eq 2) {
        return "Show the learner clearly confused at the service counter: puzzled face, furrowed brow, looking between the counter paperwork/object and staff. Add two or three small floating question marks near the learner."
    }
    if ([string]$Dialogue.id -eq "ja-repair-ticket-transfer" -and $OutputFrame -eq 2) {
        return "Show the learner clearly confused beside the ticket machine: puzzled face, furrowed brow, looking between the machine controls and station helper. Add two or three small floating question marks near the learner."
    }
    if ($OutputFrame -eq 3 -and @(
        "ja-directions-hospital",
        "ja-greeting-neighbor-transfer",
        "ja-introduce-class-transfer",
        "ja-excuse-me-cafe-transfer",
        "ja-order-bakery-review"
    ) -contains [string]$Dialogue.id) {
        $speaker = Get-VisualRoleDescription $Dialogue (Find-ScenePartnerRole $Dialogue)
        return "Make this response beat readable through $speaker's gaze, posture, and reaction."
    }
    if ([string]$Dialogue.id -eq "ja-im-sorry-small-mistake" -and $OutputFrame -eq 3) {
        return "Continue directly from frame 2: both characters remain on the ground, the recovered papers stay bundled together in their hands, and the papers must not be scattered again. Show the classmate responding kindly while accepting the bundled papers."
    }
    return ""
}

function Get-VisualRoleDescription($Dialogue, [string]$Role) {
    if ($Role -eq "learner") {
        return "the recurring female learner"
    }
    if ([string]$Dialogue.id -eq "ja-excuse-me-attention" -and ($Role -eq "staff" -or $Role -eq "passerby")) {
        return "the passerby who dropped the wallet"
    }
    if ([string]$Dialogue.id -eq "ja-directions-hospital" -and $Role -eq "local") {
        return "the paramedic / ambulance worker beside the ambulance"
    }
    if ([string]$Dialogue.id -eq "ja-greeting-neighbor-transfer" -and $Role -eq "neighbor") {
        return "the neighbor at the front gate"
    }
    if ([string]$Dialogue.id -eq "ja-introduce-class-transfer" -and $Role -eq "class_partner") {
        return "the class partner wearing a blank name tag"
    }
    if ([string]$Dialogue.id -eq "ja-excuse-me-cafe-transfer" -and $Role -eq "barista") {
        return "the waiter / barista carrying a tray"
    }
    if ([string]$Dialogue.id -eq "ja-order-bakery-review" -and $Role -eq "server") {
        return "the bakery server behind the counter"
    }
    if ([string]$Dialogue.id -eq "ja-repair-clinic-review" -and ($Role -eq "laundry_attendant" -or $Role -eq "receptionist")) {
        return "the laundry attendant beside the washing machine"
    }
    return "the $Role"
}

function Get-LocalizedPromptForDraft($PromptItem) {
    if ([string]$PromptItem.dialogue_id -eq "ja-excuse-me-attention") {
        return (Get-ExcuseMeAttentionWalletPrompt $PromptItem)
    }
    if ([string]$PromptItem.dialogue_id -ne "ja-repair-clinic-review") {
        return [string]$PromptItem.localized_prompt
    }

    $common = @"
Landscape 3:2 polished clean anime/comic panel matching visuals/style/examples/approved-comic-panel-character-free.png.

Use crisp controlled linework, warm flat colors, light environmental detail, readable human faces, and mobile-safe composition.

Use character references: visuals/style/characters/learner-reference.png for the recurring female learner avatar and visuals/style/characters/staff-reference.png for the coin laundry attendant.

Scene: bright neighborhood coin laundry with washing machines.

The learner is trying to use a coin laundry machine and does not understand the machine controls. A helpful laundry attendant stands nearby.

Mood: everyday, mildly confused, helpful.

Characters: learner: visitor with a laundry basket, coins, and detergent, unsure how to start the machine; laundry_attendant: helpful staff member beside the washing machine controls.

Visible props: row of washing machines, laundry basket, detergent bottle, coin slot, simple button panel with no readable labels.

Use landscape side-view staging for this two-person dialogue scene so both people, the machines, and their sightlines fit naturally.

Composition: natural candid comic-scene composition, not a character showcase. Characters should feel placed inside a real laundromat with believable distance, machines, counter, baskets, and sightlines. Avoid oversized foreground portraits. Camera at human eye level with medium-wide framing and enough room context to understand where both people are.

Mobile-safe composition: keep active characters, faces, hands, and key action in the central 70% of the frame and above the lower 25% so app controls do not hide them.
"@

    $lineIndex = [int]$PromptItem.line_index
    if ($lineIndex -eq 0) {
        return @"
$common

Show this beat: The laundry attendant opens the exchange and creates the need for the learner response.

Body language: laundry attendant points to the coin slot and machine start area while the learner watches, holding coins and a laundry basket, looking unsure.
"@
    }
    if ($lineIndex -eq 1) {
        return @"
$common

Show this beat: The learner needs to express that she does not understand.

Body language: learner looks puzzled, glances between the laundry attendant and the machine controls, and gently raises one open hand in a confused stop gesture while holding coins or detergent with the other hand.

Gesture cues: small head shake, open palm stop gesture; points lightly toward the machine controls, then looks back to the attendant.

Learner action: the learner should direct gaze, face angle, and gesture toward the laundry attendant or machine controls, not toward the viewer.
"@
    }
    return @"
$common

Show this beat: The laundry attendant responds so the learner can infer that help is being offered.

Body language: laundry attendant smiles and slowly points to the correct machine button or coin slot while the learner relaxes and follows along.
"@
}

function Get-ExcuseMeAttentionWalletPrompt($PromptItem) {
    $common = @"
Landscape 3:2 polished clean anime/comic panel matching visuals/style/examples/approved-comic-panel-character-free.png.

Use crisp controlled linework, warm flat colors, light environmental detail, readable human faces, and mobile-safe composition.

Scene: busy sidewalk near a small transit stop or shopping street.

A passerby has dropped a wallet while walking away, and the learner notices in time to return it.

Mood: alert, helpful, everyday, friendly.

Characters: learner: recurring female learner with her tan crossbody bag; passerby: ordinary person walking ahead, unaware their wallet has fallen.

Visible props: wallet, sidewalk, small transit stop or shopfront background, learner's tan crossbody bag.

Use landscape side-view staging for this two-person sidewalk scene so the learner, passerby, wallet, and sightlines fit naturally.

Composition: natural candid comic-scene composition, not a character showcase. Keep the learner, passerby, and wallet clearly separated and readable. Avoid oversized foreground portraits. Camera at human eye level with medium-wide framing and enough room context to understand where both people are.

Mobile-safe composition: keep active characters, faces, hands, wallet, and key action in the central 70% of the frame and above the lower 25% so app controls do not hide them.
"@

    $lineIndex = [int]$PromptItem.line_index
    if ($lineIndex -eq 0) {
        return @"
$common

Show this beat: The scene creates the need for the learner to politely get someone's attention.

Body language: passerby is walking away, not looking back. The wallet is visible on the ground behind the passerby. Learner has just spotted the wallet and looks from the wallet to the passerby with concern.

Action requirement: keep the wallet clearly visible on the ground between learner and passerby. The learner has not picked it up yet.
"@
    }
    if ($lineIndex -eq 1) {
        return @"
$common

Show this beat: The learner gets the passerby's attention politely by running up from behind with the dropped wallet.

Body language: learner approaches from behind or slightly to the side, holding the wallet forward where the passerby can see it. The passerby is beginning to turn around, surprised but not alarmed.

Learner action: the learner directs gaze, body angle, and the wallet toward the passerby, not toward the viewer.
"@
    }
    return @"
$common

Show this beat: The passerby has received the wallet back and reacts with clear gratitude.

Body language: passerby smiles with relief, holding the returned wallet close or giving a grateful small bow or nod. Learner stands nearby, relaxed and helpful.

Action requirement: the wallet is now in the passerby's hand, not on the ground.
"@
}

function Remove-SpokenBubbleConflictLanguage([string]$Prompt) {
    $clean = Remove-PromptNoise $Prompt
    $clean = $clean -replace '(?m)^Do not draw speech bubbles\. The app will overlay the .* turn bubble\.\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^Mobile-safe composition: keep active characters, faces, hands, speech bubbles, and meaning cues', 'Mobile-safe composition: keep active characters, faces, hands, and key action'
    return $clean.Trim()
}

function Remove-PromptNoise([string]$Prompt) {
    $clean = $Prompt
    $clean = $clean -replace 'Show this beat: The learner-character needs to express the target intention clearly\. Communicative function: Get attention politely\. Intention: Excuse me\.\.', 'Show this beat: The learner politely tries to get the scene partner''s attention through gaze, approach, and body language.'
    $clean = $clean -replace 'Show this beat: The learner-character needs to express the target intention clearly\. Communicative function: Say I am sorry\. Intention: I''m sorry\.\.', 'Show this beat: The learner apologizes through posture, facial expression, and a careful repair action.'
    $clean = $clean -replace 'Show this beat: The learner-character needs to express the target intention clearly\. Communicative function: Say you do not understand\. Intention: I don''t understand\.\.', 'Show this beat: The learner shows confusion through gaze, posture, and a gentle hesitation gesture.'
    $clean = $clean -replace 'Show this beat: The learner-character needs to express the target intention clearly\. Communicative function: Respond to a greeting\. Intention: Respond to Hi\.\.', 'Show this beat: The learner warmly returns the greeting through eye contact, expression, and relaxed body language.'
    $clean = $clean -replace 'Show this beat: The learner-character needs to express the target intention clearly\. Communicative function: Introduce yourself\. Intention: My name is Anna\.\.', 'Show this beat: The learner introduces herself through a polite self-presenting gesture and friendly eye contact.'
    $clean = $clean -replace 'Show this beat: The learner-character needs to express the target intention clearly\. Communicative function: Order local food\. Intention: Sandwich, please\.\.', 'Show this beat: The learner politely orders by indicating the desired food item and interacting with the server.'
    $clean = $clean -replace 'Show this beat: The learner-character needs to express the target intention clearly\. Communicative function: Ask where the hospital is\. Intention: Where is the hospital\?\.', 'Show this beat: The learner urgently asks for directions through worried eye contact, a phone map, and a searching gesture.'
    $clean = $clean -replace 'Communicative function:\s*[^.]+\.\s*Intention:\s*[^.\r\n]+\.*', ''
    $clean = $clean -replace '\s*Intention:\s*[^\r\n]+', ''
    $clean = $clean -replace '\bwhile saying\b\s+[^.;,\r\n]+', 'with nonverbal expression'
    $clean = $clean -replace '\bstarts saying\b\s+[^.;,\r\n]+', 'reacts with nonverbal expression'
    $clean = $clean -replace '\bsaying sorry\b', 'showing an apologetic expression'
    $clean = $clean -replace '(?m)^Do not draw speech bubbles\..*\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^.*speech bubbles?.*\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^.*Speech bubble.*\r?\n\r?\n?', ''
    $clean = $clean -replace '\s*Meaning cues:[^\r\n.]*\.', '.'
    $clean = $clean -replace ' A small symbolic confusion cue such as floating question marks or a simple puzzled icon appears near the learner, without translations or dialogue text\.', ''
    $clean = $clean -replace 'A small symbolic confusion cue such as floating question marks or a simple puzzled icon appears near the learner, without translations or dialogue text\.', ''
    $clean = $clean -replace '(?m)^Localize the environment as: .*\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^Draw exactly one clean comic speech bubble attached to .*? The speech bubble must contain only three dots: \.\.\.\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^Good-copy frame \d+ requirement: .*?\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^Reject rough sketchbook style, children''s-book style, thick marker outlines, decorative sketch borders, photorealism, app screenshot layouts, close-up portraits, sticker poses, reaction shots, character reference sheets, staged two-character poses, and generic character drift\.\r?\n\r?\n?', ''
    $clean = $clean -replace '(?m)^Use culturally ordinary clothing, posture, and interpersonal distance for the scene context, but keep the communicative function language-neutral unless the scene explicitly requires a local cultural variant\.\r?\n\r?\n?', ''
    $removePrefixes = @(
        "Draw exactly one clean comic speech bubble",
        "Use character references:",
        "No subtitles, no translations",
        "Do not render the dialogue",
        "Good-copy frame ",
        "The image must teach meaning",
        "Reject rough sketchbook style",
        "Use culturally ordinary clothing",
        "Localize the environment as:"
    )
    $lines = @($clean -split "\r?\n" | Where-Object {
        $line = $_
        -not (@($removePrefixes | Where-Object { $line.StartsWith($_) }).Count)
    } | ForEach-Object {
        Remove-GestureCueLabels $_
    })
    return ($lines -join "`n")
}

function Remove-GestureCueLabels([string]$Line) {
    $prefix = "Gesture cues:"
    if (-not $Line.StartsWith($prefix)) {
        return $Line
    }

    $body = $Line.Substring($prefix.Length).Trim()
    $parts = @($body -split ';' | ForEach-Object {
        $part = $_.Trim()
        if ($part -match '^[A-Za-z_]+:\s*(.+)$') {
            return $Matches[1].Trim().TrimEnd(".")
        }
        return $part.TrimEnd(".")
    } | Where-Object { $_ })

    if ($parts.Count -eq 0) {
        return $Line
    }
    return "$prefix $($parts -join '; ')."
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
    $outDir = Split-Path -Parent $OutPath
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
    [System.IO.File]::WriteAllBytes($OutPath, [Convert]::FromBase64String($b64))
}

$secrets = Read-JsonFile $SecretsPath
$apiKey = [string]$secrets.OPENAI_API_KEY
if (-not $apiKey) {
    throw "OPENAI_API_KEY missing from $SecretsPath"
}

$dialogues = Read-JsonFile $DataPath
$promptManifest = Read-JsonFile $PromptsPath
$dialogueById = @{}
foreach ($dialogue in $dialogues.dialogues) {
    $dialogueById[[string]$dialogue.id] = $dialogue
}

$dialogueIdsToGenerate = if ($OnlyDialogue) { @($OnlyDialogue) } else { $FullRegenerationDialogues }

$jobs = @()
foreach ($dialogueId in $dialogueIdsToGenerate) {
    $dialogue = $dialogueById[$dialogueId]
    if (-not $dialogue) { throw "Missing dialogue $dialogueId" }
    if ($OnlyFrame -eq 0) {
        $jobs += @{ DialogueId = $dialogueId; OutputFrame = 0; SourceLine = 0; Base = $true; Note = "" }
    }
    for ($lineIndex = 0; $lineIndex -lt 3; $lineIndex++) {
        $jobs += @{ DialogueId = $dialogueId; OutputFrame = ($lineIndex + 1); SourceLine = $lineIndex; Base = $false; Note = "" }
    }
}
foreach ($fix in $SingleFrameFixes) {
    if ($OnlyDialogue -and $fix.DialogueId -ne $OnlyDialogue) { continue }
    if ($FullRegenerationDialogues -contains $fix.DialogueId) { continue }
    $jobs += $fix
}
if ($OnlyFrame -ge 0) {
    $jobs = @($jobs | Where-Object { [int]$_.OutputFrame -eq $OnlyFrame })
}
if ($Limit -gt 0) {
    $jobs = @($jobs | Select-Object -First $Limit)
}

$created = 0
$skipped = 0
foreach ($job in $jobs) {
    $dialogue = $dialogueById[[string]$job.DialogueId]
    $lineIndex = [int]$job.SourceLine
    $outputFrame = [int]$job.OutputFrame
    $line = @($dialogue.lines | Where-Object { [int]$_.index -eq $lineIndex })[0]
    $promptItem = Get-PromptItem $promptManifest $job.DialogueId $lineIndex
    $outPath = Join-Path $ResolvedOutputRoot ("{0}/frame-{1}.png" -f $job.DialogueId, $outputFrame)
    if ((Test-Path -LiteralPath $outPath) -and -not $Force -and -not $PromptOnly) {
        Write-Host "skip $((Relative-Path $outPath))"
        $skipped += 1
        continue
    }

    $partnerReference = Find-PartnerReference $dialogue $line
    $references = @(
        (Join-Path $CharacterDir "learner-reference.png"),
        $partnerReference
    )
    if ($outputFrame -le 1 -and (Test-Path -LiteralPath $StyleReference)) {
        $references = @($StyleReference) + $references
    }
    if ($outputFrame -gt 1) {
        $anchorFrame = Get-ContinuityAnchorFrame $dialogue $outputFrame
        $anchorPath = Join-Path $ResolvedOutputRoot ("{0}/frame-{1}.png" -f $job.DialogueId, $anchorFrame)
        if (Test-Path -LiteralPath $anchorPath) {
            $references += $anchorPath
        }
    }
    $prompt = if ($job.Base) {
        Build-BasePrompt $promptItem $dialogue
    } else {
        Build-SpokenPrompt $promptItem $dialogue $line $outputFrame ([string]$job.Note)
    }
    $promptPath = Join-Path (Split-Path -Parent $outPath) ("prompt-frame-{0}.txt" -f $outputFrame)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $outPath) | Out-Null
    [System.IO.File]::WriteAllText($promptPath, $prompt, [System.Text.UTF8Encoding]::new($false))
    if ($PromptOnly) {
        Write-Host "prompt $((Relative-Path $promptPath))"
        $created += 1
        continue
    }
    Write-Host "generate $((Relative-Path $outPath))"
    Invoke-ImageEdit $apiKey $prompt $outPath $references
    $created += 1
}

Write-Host "created=$created skipped=$skipped"
