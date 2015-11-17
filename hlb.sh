hlb() {
   	mkdir -p har
   	passed=0
	for i in `seq 1 $1`
   	do
	   	files=`ls har | wc -l`
		echo "Test $i starting.."
	   	r $2
	   	after_files=`ls har | wc -l`
	   	hars=$(($after_files - $files))
		echo "$(($after_files - $files)) har file(s) generated" 
	   	passed=$(($passed + $hars / 3))
   	done
   	printf "$passed/$1 passed\n"
}

r() {
	if [ $1 ]; then
		echo "$1"
		python hlb_test.py "$1"
	else
		python hlb_test.py -f input_list.txt
	fi
}


