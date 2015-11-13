from hlb_pi import HeadlessBrowser
import sys
import os


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "need at least one url"
        raise SystemExit
    print sys.argv
    hlb = HeadlessBrowser()
    hlb.run(input_list=sys.argv[1:])
