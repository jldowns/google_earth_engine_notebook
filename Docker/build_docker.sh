VERSION=1.0

docker build -t jldowns/google_earth_engine_notebook:$VERSION .
docker push jldowns/google_earth_engine_notebook:$VERSION


echo "Don't forget to update the README to version $VERSION"
