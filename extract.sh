echo "Removing old data..."
rm -rf ignores
mkdir ignores
echo "Extracting data..."
for f in raw_data/*.zip; do
    name=$(echo ${f##*/} | sed 's/\.[^\.]*$//')
    mkdir ignores/$name
    unzip -qq $f ".gitignore" -d ignores/$name
    mv ignores/$name/.gitignore ignores/$name/gitignore
done