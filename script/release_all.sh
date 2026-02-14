#!/bin/bash
set -e

# Quick release script - commits all changes, tags, and releases
# Usage: ./scripts/release_all.sh <version> <commit_message> [release_notes]
# Example: ./scripts/release_all.sh 3.3.1 "Fix signed integer handling"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 <version> <commit_message> [release_notes]"
    echo "Example: $0 3.3.1 \"Fix signed integer handling\" \"Fixes RW register bug\""
    exit 1
fi

VERSION="$1"
COMMIT_MSG="$2"
RELEASE_NOTES="${3:-$COMMIT_MSG}"

# Remove 'v' prefix if present
VERSION="${VERSION#v}"

echo "🚀 Quick releasing version v$VERSION"

# Show what will be committed
echo "📋 Changes to be committed:"
git status --short

# Add all changes
echo "➕ Adding all changes"
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "⚠️  No changes to commit"
    exit 0
fi

# Update manifest.json version
echo "📝 Updating manifest.json to version $VERSION"
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" custom_components/sprsun_modbus/manifest.json

# Add manifest changes
git add custom_components/sprsun_modbus/manifest.json

# Commit all changes
echo "💾 Committing all changes"
git commit -m "$COMMIT_MSG"

# Create tag
echo "🏷️  Creating tag v$VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION

$RELEASE_NOTES"

# Push changes and tag
echo "⬆️  Pushing to GitHub"
git push
git push origin "v$VERSION"

# Create GitHub release
echo "📦 Creating GitHub release"
gh release create "v$VERSION" \
    --title "v$VERSION" \
    --notes "$RELEASE_NOTES" \
    --latest

echo "✅ Release v$VERSION completed successfully!"
echo "🔗 https://github.com/stasek44/sprsun-modbus/releases/tag/v$VERSION"
