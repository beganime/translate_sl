param(
    [string]$KeyPath = "$HOME\.ssh\translatesl_deploy_ed25519"
)

$ErrorActionPreference = "Stop"

if ((Test-Path $KeyPath) -or (Test-Path "$KeyPath.pub")) {
    throw "Ключ уже существует: $KeyPath. Не перезаписываю его."
}

$sshDir = Split-Path -Parent $KeyPath
New-Item -ItemType Directory -Force -Path $sshDir | Out-Null

$sshKeygen = Get-Command ssh-keygen -ErrorAction Stop
$keygenProcess = Start-Process -FilePath $sshKeygen.Source -Wait -NoNewWindow -PassThru -ArgumentList @(
    "-t", "ed25519", "-f", $KeyPath, "-N", '""', "-C", "translatesl-temporary-deploy"
)
if ($keygenProcess.ExitCode -ne 0 -or -not (Test-Path "$KeyPath.pub")) {
    throw "Не удалось создать SSH-ключ. Файлы ключа не были использованы."
}

$publicKey = (Get-Content -Raw "$KeyPath.pub").Trim()

Write-Host "`nПубличный ключ создан. Приватный ключ не отправляйте в чат и никому не передавайте." -ForegroundColor Yellow
Write-Host "`nНа сервере войдите под root и выполните одну команду:" -ForegroundColor Cyan
Write-Host ""
Write-Host "adduser --disabled-password --gecos '' translatesl-deploy; usermod -aG sudo translatesl-deploy; install -d -m 700 -o translatesl-deploy -g translatesl-deploy /home/translatesl-deploy/.ssh; echo '$publicKey' > /home/translatesl-deploy/.ssh/authorized_keys; chown translatesl-deploy:translatesl-deploy /home/translatesl-deploy/.ssh/authorized_keys; chmod 600 /home/translatesl-deploy/.ssh/authorized_keys; printf 'translatesl-deploy ALL=(ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/translatesl-deploy; chmod 440 /etc/sudoers.d/translatesl-deploy; visudo -cf /etc/sudoers.d/translatesl-deploy"
Write-Host ""
Write-Host "После этого напишите мне «готово». Я подключусь как translatesl-deploy@72.62.37.145 и сначала только просмотрю Docker/диск/веб-сервер." -ForegroundColor Green
Write-Host "`nПосле завершения удалите временный доступ на сервере:" -ForegroundColor Cyan
Write-Host "rm -f /etc/sudoers.d/translatesl-deploy; deluser --remove-home translatesl-deploy"
