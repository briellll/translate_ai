Param([ValidateSet('onedir','onefile')][string]$mode='onedir')
$opts = if ($mode -eq 'onedir') { '--onedir' } else { '--onefile' }
pyinstaller --noconfirm $opts --windowed --name TradutorAI --collect-all customtkinter translator\gui_app.py
