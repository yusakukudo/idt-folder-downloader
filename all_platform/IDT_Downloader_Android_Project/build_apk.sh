#!/bin/bash
# ====================================================
# Build Script for Android APK
# ====================================================
set -e

echo "📱 Building Android APK..."

if command -v ./gradlew &> /dev/null; then
    ./gradlew assembleDebug
elif command -v gradle &> /dev/null; then
    gradle assembleDebug
else
    echo "💡 Gradle wrapper not found. You can build the APK by opening this folder in Android Studio and clicking 'Build > Build Bundle(s) / APK(s) > Build APK(s)'."
    exit 0
fi

echo "✨ APK built successfully at: app/build/outputs/apk/debug/app-debug.apk"
