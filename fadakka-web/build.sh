#!/bin/bash
# Build script for React app

echo "Installing dependencies..."
npm install

echo "Building React app..."
npm run build

echo "Build complete!"