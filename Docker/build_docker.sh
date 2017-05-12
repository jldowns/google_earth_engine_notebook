VERSION=1.1

docker build -t jldowns/google_earth_engine_notebook:$VERSION .
docker push jldowns/google_earth_engine_notebook:$VERSION


echo "Don't forget to update to version $VERSION:"
echo "  - README"
echo "  - start_gee_notebook.sh"
echo "  - authenticate_gee.sh"
