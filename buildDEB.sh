#!/usr/bin/env bash

app_name=PyLibSuitETECSA
app_version=0.1.2
module_name=libsuitetecsa

temp_dir=$app_name'_'$app_version'_all'
debian_dir="$temp_dir//DEBIAN"

if [ -d $debian_dir ]; then
  echo "El directorio existe."
else
  mkdir -p $debian_dir
fi

cp BuildDEB/* $debian_dir

dirs=($(find $module_name/ -type d))
for i in "${dirs[@]}"; do
    if [ "$(basename "$i")" == __pycache__ ]; then
        echo "$i"
        rm -rf "$i"
    else
        mkdir -p $temp_dir/usr/lib/python3/site-packages/"$i"
    fi
done

files=($(find $module_name/ -type f))
for i in "${files[@]}"; do
    if [ "${i:(-3)}" == .py ]; then
        cp "$i" $temp_dir/usr/lib/python3/site-packages/"$i"
    fi
done

chmod 775 -R $debian_dir
dpkg-deb -b $temp_dir
rm -r $temp_dir
