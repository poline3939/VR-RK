#! /bin/bash
root_folder=`pwd`/spipy

# get opts
SKIP_COMPILE=0
while getopts ":xh" opt; do
	case $opt in
		x)
			SKIP_COMPILE=1
			;;
		h)
			echo "Use : ./make_all.sh [-x] (skip compiling MPI part)"
			echo "                    [-h] (help info)"
			exit 0
			;;
		\?)
			echo "[Error] Invalid option : $OPTARG . Exit."
			exit 1
			;;
	esac
done

# check whether there is anaconda installed
Ana_path=`which python`
a='anaconda'
b='miniconda'
if [[ $Ana_path =~ $a ]] || [[ $Ana_path =~ $b ]]
then
	echo "[Info] Root folder is $root_folder"
else
	echo "[Error] Use anaconda2/miniconda2 please. Exit."
	exit 1
fi
py_version=`conda list | grep "python"`
a='2.7'
if [[ $py_version =~ $a ]]
then
	echo "==> Anaconda version authorized"
else
	echo "[Error] Your python version is $py_version. Exit."
	exit 1
fi


# decide your system
echo "==> Authorizing operating system"
sys=`uname`

if [ $sys != "Linux" ] && [ $sys != "Darwin" ]
then
	echo "[Error] I can't recognize your system. Exit."
	exit 1
fi

if [ $sys = "Darwin" ] && [ $SKIP_COMPILE -ne 1 ]
then
	echo "[Warning] Since now I didn't add any support on compiling EMC module in MacOS, '-x' option will be added automatically. Continue ? (y/n)"
	read answer
	if [ answer = "n" ]; then
		exit 1
	fi
	SKIP_COMPILE=1
fi

if [ $SKIP_COMPILE -eq 1 ]; then
	echo "[Info] Skip compiling merge.emc and simulate.sim module."
fi


# decide mpicc
if [ $SKIP_COMPILE -eq 0 ]; then
	echo "==> Authorizing MPI"
	# decide your gcc
	if [ $sys = "Darwin" ]
	then
		nowgcc=`which gcc`
		echo "[Warning] I need openmp and MPI support. Do you want to use current gcc? : $nowgcc [y/n]"
		flag=0
		while [ $flag = 0 ]
		do
			read answer
			if [ $answer = "n" ]
			then
				echo "Give me your specific gcc path : "
				read mygcc
				flag=1
			elif [ $answer = "y" ]
			then
				mygcc=gcc
				flag=1
			else
				echo "[Warning] Please give 'y' or 'n'."
			fi
		done
	fi
	# reject conda mpi
	if [ $sys = "Linux" ]
	then
		nowmpicc=`which mpicc`
		nowmpirun=`which mpirun`
		if [ $nowmpicc = "${Ana_path%/bin/python*}/bin/mpicc" ] || [ $nowmpirun = "${Ana_path%/bin/python*}/bin/mpirun" ]
		then
			echo "[Warning] The default mpicc is $nowmpicc"
			echo "   Since it is from conda env, problems may occur while using it."
			echo "   Please give me another mpicc absolute path (type 'n' to exit) : "
			read mympicc
			if [ $mympicc = "n" ]
			then
				exit 1
			fi
		else
			mympicc=$nowmpicc
		fi
		# record mpirun
		mympirun=`dirname $mympicc`/mpirun
	fi
fi

# start compiling ...
echo "==> Compile image/bhtsne_source"
cd $root_folder/image/bhtsne_source
g++ sptree.cpp tsne.cpp tsne_main.cpp -o bh_tsne -O2
if [ $? -ne 0 ];then echo $?; exit 1;fi
chmod u+x bh_tsne


if [ $SKIP_COMPILE -eq 0 ]; then

	echo "==> Compile merge/template_emc/src"
	cd $root_folder/merge/template_emc/src
	chmod u+x compile.sh ../new_project
	if [ $sys = "Linux" ]
	then
		$mympicc -fopenmp recon.c setup.c max.c quat.c interp.c -o emc_LINUX -I ./ -lgsl -lgslcblas -lm -O3
		if [ $? -ne 0 ];then echo $?; exit 1;fi
		chmod u+x emc_LINUX
	elif [ $sys = "Darwin" ]
	then
		$mygcc -fopenmp recon.c setup.c max.c quat.c interp.c -o emc_MAC -I ./ -lgsl -lgslcblas -lm -O3 -lmpi
		if [ $? -ne 0 ];then echo $?; exit 1;fi
		chmod u+x emc_MAC
	fi


	echo "==> Compile simulate/src"
	cd $root_folder/simulate/src
	chmod u+x compile.sh ../code/make_densities.py ../code/make_detector.py ../code/make_intensities.py
	if [ $sys = "Linux" ]
	then
		$mympicc -fopenmp make_data.c -o make_data_LINUX -I ./ -lgsl -lgslcblas -lm -O3
		if [ $? -ne 0 ];then echo $?; exit 1;fi
		chmod u+x make_data_LINUX
	elif [ $sys = "Darwin" ]
	then
		$mygcc -fopenmp make_data.c -o make_data_MAC -I ./ -lgsl -lgslcblas -lm -O3
		if [ $? -ne 0 ];then echo $?; exit 1;fi
		chmod u+x make_data_MAC
	fi

fi


echo "==> Checking python packages"
echo "[Warning] The coming procedure may install packages into your conda environment. Continue ? (y/n)"
read answer
if [ $answer = "n" ]
then
	exit 1
fi

echo "... numpy"
tmp=`conda list | grep "numpy"`
if [ -z "$tmp" ];then conda install numpy;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... scipy"
tmp=`conda list | grep "scipy"`
if [ -z "$tmp" ];then conda install scipy;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... scikit-learn"
tmp=`conda list | grep "scikit-learn"`
if [ -z "$tmp" ];then conda install scikit-learn;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... matplotlib"
tmp=`conda list | grep "matplotlib"`
if [ -z "$tmp" ];then conda install matplotlib;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... h5py"
tmp=`conda list | grep "h5py"`
if [ -z "$tmp" ];then conda install h5py;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... numexpr"
tmp=`conda list | grep "numexpr"`
if [ -z "$tmp" ];then conda install numexpr;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... psutil"
tmp=`conda list | grep "psutil"`
if [ -z "$tmp" ];then conda install psutil;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... mrcfile"
tmp=`conda list | grep "mrcfile"`
if [ -z "$tmp" ];then pip install mrcfile;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... openmpi"
tmp=`conda list | grep "openmpi"`
if [ -z "$tmp" ];then conda install -c conda-forge openmpi;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi

echo "... mpi4py"
tmp=`conda list | grep "mpi4py"`
if [ -z "$tmp" ];then conda install -c conda-forge mpi4py;fi
if [ $? -ne 0 ];then echo $?; exit 1;fi


echo "==> others"
cd $root_folder/phase
chmod u+x ./template_2d/new_project ./template_3d/new_project
cd $root_folder/image/qlist_dir
chmod u+x ./gen_quat

# make soft link
if [ ! -d "${Ana_path%/bin/python*}/lib/python2.7/site-packages/spipy" ]
then
	ln -fs $root_folder ${Ana_path%/bin/python*}/lib/python2.7/site-packages/spipy
else
	echo "[Warning] spipy is already in python2.7/site-packages. Over-write it? [y/n]"
	flag=0
	while [ $flag = 0 ]
	do
		read overwrite
		if [ $overwrite = "y" ]
		then
			rm ${Ana_path%/bin/python*}/lib/python2.7/site-packages/spipy
			ln -fs $root_folder ${Ana_path%/bin/python*}/lib/python2.7/site-packages/spipy
			flag=1
		elif [ $overwrite = "n" ]
		then
			echo "Skip."
			flag=1
		else
			echo "[Warning] Please give 'y' or 'n'."
		fi
	done
fi

# write info.py :
INFO=$root_folder/info.py
if [ -f "$INFO" ]; then
	rm -rf $INFO
fi
touch $INFO
# version
echo "VERSION = 2.1" >> $INFO
# mympirun
if [ $SKIP_COMPILE -eq 0 ]; then
	echo "EMC_MPI = '$mympirun'" >> $INFO
fi


echo "==> Complete!"
