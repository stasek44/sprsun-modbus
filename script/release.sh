#!/bin/bash
set -e

# Auto release script for SPRSUN integration
# Usage: ./scripts/release.sh <version> [release notes]
# Example: ./scripts/release.sh 2.0.2 "Fix sensor readings"

if [ -z "$1" ]; then
    echo "Usage: $0 <version> [release_notes]"
    echo "Example: $0 2.0.2 \"Fix sensor readings\""
    exit 1
fi

VERSION="$1"
RELEASE_NOTES="${2:-Release v$VERSION}"

# Remove 'v' prefix if present
VERSION="${VERSION#v}"

echo "🚀 Releasing version v$VERSION"

# Update manifest.json version
echo "📝 Updating manifest.json to version $VERSION"
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" custom_components/sprsun/manifest.json

# Commit changes
echo "💾 Committing changes"
git add custom_components/sprsun/manifest.json
git commit -m "Release v$VERSION

$RELEASE_NOTES"

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
echo "🔗 https://github.com/stasek44/sprsun/releases/tag/v$VERSION"
