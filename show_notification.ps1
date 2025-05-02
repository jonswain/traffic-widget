param(
    [string]$Title,
    [string]$Message
)

$ImagePath = 'C:\Path\to\icon.jpg'

New-BurntToastNotification -Text $Title, $Message -AppLogo $ImagePath -Sound Alarm5