# W bieżącym katalogu
find . -name ".env" -type f -exec grep -l "rtsp" {} \;

# W konkretnej ścieżce
find ~/github -name ".env" -type f -exec grep -l "rtsp" {} \;