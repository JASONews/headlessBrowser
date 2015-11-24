hb-start() {
   	mkdir -p har
   	passed=0
	sites=`cat input_list.txt | wc -l`
	for i in `seq 1 $1`
   	do
	   	files=`ls har | wc -l`
		echo "Test $i starting.."
	   	hb-run $2
	   	after_files=`ls har | wc -l`
	   	hars=$(($after_files - $files))
		echo "$(($after_files - $files)) har file(s) generated" 
	   	passed=$(($passed + $hars / $sites))
   	done
   	printf "$passed/$1 passed\n"
}

hb-run() {
	if [ $1 ]; then
		echo "$1"
		python hb_test.py "$1"
	else
		python hb_test.py -f input_list.txt
	fi
}

hb-clean() {
	rm -fr har htmls screenshots hb_results.json
}
