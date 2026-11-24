@echo off
setlocal
echo =========================================================================
echo   Pushing All Exercises + Capstone Docker Images to Docker Hub
echo =========================================================================
echo Target Repositories:
echo   - https://hub.docker.com/r/shashankreddy30/threat-intel-app
echo   - https://hub.docker.com/r/shashankreddy30/mongodb-nosql-labs-and-capstone
echo.

docker push shashankreddy30/threat-intel-app:latest
docker push shashankreddy30/mongodb-nosql-labs-and-capstone:latest

echo.
echo =========================================================================
echo   [SUCCESS] Docker Hub images pushed!
echo   Single Link: https://hub.docker.com/r/shashankreddy30/threat-intel-app
echo   Unified Link: https://hub.docker.com/r/shashankreddy30/mongodb-nosql-labs-and-capstone
echo =========================================================================
pause
