#!/bin/bash
set -xe

install_dependencies() {

    if [[ $OSTYPE == 'darwin'* ]]; then

        # Check system architecture
        ARCH=$(uname -m)
        JAVA_URL=""
        if [[ "$ARCH" == "x86_64" ]]; then
            JAVA_URL="https://download.oracle.com/java/22/archive/jdk-22.0.2_macos-x64_bin.tar.gz"
        elif [[ "$ARCH" == "arm64" ]]; then
            JAVA_URL="https://download.java.net/java/GA/jdk22.0.2/c9ecb94cd31b495da20a27d4581645e8/9/GPL/openjdk-22.0.2_macos-aarch64_bin.tar.gz"
        else
            echo "Error: Unsupported architecture ($ARCH)."
            exit 1
        fi

        JAVA_TAR="openjdk-22.0.2_macos-aarch64_bin.tar.gz"
        INSTALL_DIR="/Library/Java/JavaVirtualMachines"

        # Download OpenJDK
        curl -L -o "$JAVA_TAR" "$JAVA_URL"

        # Extract and move to system location
        sudo mkdir -p "$INSTALL_DIR"
        sudo tar -xzf "$JAVA_TAR" -C "$INSTALL_DIR"
        sudo rm -rf "$INSTALL_DIR"/openjdk.jdk

        # Cleanup tar file
        rm "$JAVA_TAR"

        # Ensure JAVA_HOME is set correctly
        export JAVA_HOME="$INSTALL_DIR/jdk-22.0.2.jdk/Contents/Home"

        brew update
        brew install maven


        # Verify installation
        mvn --version

    elif command -v apt &> /dev/null; then
        # Debian/Ubuntu based
        sudo apt update
        sudo apt install -y default-jre default-jdk maven
        sudo apt install -y python3 python3-pip python3-venv
    else
        echo "Error: neither apt nor yum found. Java installation failed."
        exit 1
    fi

    if ! command -v java &> /dev/null; then
        echo "Error: Java installation failed."
        exit 1
    fi
    echo "Java successfully installed."
    java --version
}

install_dependencies
