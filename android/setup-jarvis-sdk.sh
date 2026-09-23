#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "========================================"
echo " JARVIS ANDROID APK MASTER SETUP"
echo " ARM64 TERMUX"
echo "========================================"

SDK="$HOME/Jarvis/android-sdk"

echo "[1/12] Checking Java..."
java -version

echo "[2/12] Installing native Android tools..."
pkg update -y
pkg install wget unzip aapt aapt2 aidl d8 apksigner -y

echo "[3/12] Creating SDK..."
mkdir -p "$SDK/platforms/android-35"
mkdir -p "$SDK/build-tools/35.0.1"

echo "[4/12] Downloading Android API 35..."
cd "$HOME"

wget -c \
  https://dl.google.com/android/repository/platform-35_r02.zip \
  -O platform-35_r02.zip

echo "[5/12] Extracting API 35..."
rm -rf "$SDK/platforms/android-35"
mkdir -p "$SDK/platforms/android-35"

unzip -q platform-35_r02.zip \
  -d "$SDK/platform-temp"

cp -r "$SDK/platform-temp/android-35/"* \
  "$SDK/platforms/android-35/"

rm -rf "$SDK/platform-temp"
rm -f platform-35_r02.zip

echo "[6/12] Checking android.jar..."
test -f "$SDK/platforms/android-35/android.jar"

echo "[7/12] Creating Termux build-tools bridge..."
BT="$SDK/build-tools/35.0.1"

ln -sf "$(command -v aapt)" "$BT/aapt"
ln -sf "$(command -v aapt2)" "$BT/aapt2"
ln -sf "$(command -v aidl)" "$BT/aidl"
ln -sf "$(command -v d8)" "$BT/d8"
ln -sf "$(command -v apksigner)" "$BT/apksigner"

cat > "$BT/source.properties" <<'EOF'
Pkg.Desc=Android SDK Build-Tools
Pkg.Revision=35.0.1
Pkg.Path=build-tools;35.0.1
EOF

echo "[8/12] Creating SDK metadata..."
cat > "$SDK/source.properties" <<'EOF'
Pkg.Desc=Android SDK
Pkg.Revision=35
EOF

echo "[9/12] Creating local.properties..."
cd "$HOME/Jarvis/android"

printf 'sdk.dir=%s\n' "$SDK" > local.properties

echo "[10/12] Setting environment..."
export ANDROID_HOME="$SDK"
export ANDROID_SDK_ROOT="$SDK"
export PATH="$BT:$HOME/.gradle/bin:$PATH"

echo "[11/12] Verifying SDK..."
echo "ANDROID_HOME=$ANDROID_HOME"

test -f "$SDK/platforms/android-35/android.jar"

echo "android.jar: OK"
echo "aapt:       $(command -v aapt)"
echo "aapt2:      $(command -v aapt2)"
echo "aidl:       $(command -v aidl)"
echo "d8:         $(command -v d8)"
echo "apksigner:  $(command -v apksigner)"

echo "[12/12] Testing Gradle..."
cd "$HOME/Jarvis/android"

gradle --stop || true

gradle assembleDebug --no-daemon

echo
echo "========================================"
echo " JARVIS APK BUILD FINISHED"
echo "========================================"

APK="$HOME/Jarvis/android/app/build/outputs/apk/debug/app-debug.apk"

if [ -f "$APK" ]; then
    echo
    echo "APK FOUND:"
    echo "$APK"
    echo
    ls -lh "$APK"
else
    echo
    echo "BUILD COMPLETED BUT APK WAS NOT FOUND."
    echo "Check Gradle output above."
fi
