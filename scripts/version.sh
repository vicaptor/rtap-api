#!/bin/bash

# Function to validate version number format
validate_version() {
    if [[ ! $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo "Error: Version must be in format X.Y.Z (e.g., 1.0.0)"
        exit 1
    fi
}

# Function to get the current date from date.txt
get_current_date() {
    if [ ! -f "date.txt" ]; then
        echo "Error: date.txt not found. Please run the script that generates it first."
        exit 1
    fi
    cat date.txt
}

# Function to get current version from CHANGELOG.md
get_current_version() {
    grep -m 1 "## \[" CHANGELOG.md | grep -o "\[.*\]" | tr -d '[]'
}

# Function to get current changes from CHANGELOG.md
get_current_changes() {
    # Extract all content between the first version header and the next version header or EOF
    awk '/^## \[/{p++;next} p==1{print}' CHANGELOG.md | \
    sed '/^## \[/,$d' | \
    awk 'NF' | \
    sed 's/^### /\n### /' | \
    awk 'NF' # Remove empty lines
}

# Function to extract latest changes from CHANGELOG.md
get_latest_changes() {
    # Extract content between the first two ## headers, skip the version line
    awk '/^## \[/{p++;next} p==1{print}' CHANGELOG.md | \
    awk 'NF' | \
    sed 's/^### /\n### /' | \
    awk 'NF' # Remove empty lines
}

# Function to update the last version's date
update_last_version_date() {
    local current_date=$(get_current_date)
    # Get the last version number and update its date
    local last_version=$(get_current_version)
    if [ ! -z "$last_version" ]; then
        sed -i "0,/## \[$last_version\] - [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/s/## \[$last_version\] - [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}/## [$last_version] - $current_date/" CHANGELOG.md
    fi
}

# Function to update version in package files
update_version() {
    local new_version=$1
    local date=$(get_current_date)
    
    # First update the last version's date
    update_last_version_date
    
    # Then add the new version entry
    local temp_file=$(mktemp)
    echo "## [$new_version] - $date" > "$temp_file"
    echo "" >> "$temp_file"
    echo "### Added" >> "$temp_file"
    echo "- " >> "$temp_file"
    echo "" >> "$temp_file"
    echo "### Changed" >> "$temp_file"
    echo "- " >> "$temp_file"
    echo "" >> "$temp_file"
    echo "### Deprecated" >> "$temp_file"
    echo "- " >> "$temp_file"
    echo "" >> "$temp_file"
    echo "### Removed" >> "$temp_file"
    echo "- " >> "$temp_file"
    echo "" >> "$temp_file"
    echo "### Fixed" >> "$temp_file"
    echo "- " >> "$temp_file"
    echo "" >> "$temp_file"
    echo "### Security" >> "$temp_file"
    echo "- " >> "$temp_file"
    echo "" >> "$temp_file"
    cat CHANGELOG.md >> "$temp_file"
    mv "$temp_file" CHANGELOG.md

    # If package.json exists in annotation service, update it
    if [ -f "services/annotation-service/package.json" ]; then
        sed -i "s/\"version\": \".*\"/\"version\": \"$new_version\"/" services/annotation-service/package.json
    fi

    # If version.go exists in rtsp server, update it
    if [ -f "services/rtsp-server/version.go" ]; then
        sed -i "s/const Version = \".*\"/const Version = \"$new_version\"/" services/rtsp-server/version.go
    fi
}

# Function to create git tag and push changes
tag_and_push() {
    local new_version=$1
    local base_message=$2
    local changes=$(get_latest_changes)
    
    # Prepare commit message with version and latest changes
    local commit_message="chore: bump version to $new_version

$changes

$base_message"

    # Stage changes
    git add CHANGELOG.md
    git add services/annotation-service/package.json 2>/dev/null || true
    git add services/rtsp-server/version.go 2>/dev/null || true

    # Commit changes with the full message
    git commit -m "$commit_message"

    # Create tag with the same message
    git tag -a "v$new_version" -m "$commit_message"
    
    echo "Pushing changes and tags to remote repository..."
    
    # Push both the changes and the tags
    git push && git push --tags
    
    if [ $? -eq 0 ]; then
        echo "Successfully pushed changes and tags to remote repository"
    else
        echo "Error: Failed to push changes to remote repository"
        exit 1
    fi
}

# Main script
# Ensure we're in the project root
if [ ! -f "CHANGELOG.md" ]; then
    echo "Error: Must be run from project root directory"
    exit 1
fi

# Get default values from CHANGELOG.md
DEFAULT_VERSION=$(get_current_version)
DEFAULT_MESSAGE=$(get_current_changes)

# Use command line arguments if provided, otherwise use defaults
VERSION="${1:-$DEFAULT_VERSION}"
MESSAGE="${2:-$DEFAULT_MESSAGE}"

# Show what we're using
echo "Using version: $VERSION"
echo "Using changes:"
echo "$MESSAGE"
echo

# Validate version format
validate_version "$VERSION"

# Update version in files
update_version "$VERSION"

# Create git tag and commit changes, then push to remote
tag_and_push "$VERSION" "$MESSAGE"

echo "Version update complete and pushed to remote repository!"
