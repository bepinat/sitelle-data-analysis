This release of ORB/ORBS/ORCS is from the version provided by Thomas Martin (https://github.com/thomasorb) at the date of April 1st 2024.

The intent of this package is to have a fully workable version of ORCS. ORBS has not been tested and my not be necessary. Nevertheless, this package may be merged in the future with the software suite used at CFHT to perform the reduction of SITELLE data with ORBS, so that one single package enable to reduce and analyse the data.

In order to install the package properly, an environment has to be set. We have compiled all version of package that enable the software to run properly.

One can define an environment name (conda environment) and specify the repository where it will be installed in the user home directory ($HOME):

    envname='orb3'
    python_folder='python_programs'

First, it is necessary to install Miniconda to create the proper python environment with the appropriate package versions:

    mkdir -p ~/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    rm -rf ~/miniconda3/miniconda.sh
    ~/miniconda3/bin/conda init bash
    . .bashrc

The environment can then be created and activated:

    conda create -n $envname
    conda activate $envname

Once this is done, it is time to install the required python packages.

Packages necessary for ORB:

    conda install -c conda-forge -c astropy -c anaconda python=3.9.7 ipython astropy=5.3.4 numpy=1.24.3 scipy=1.10.1 matplotlib=3.5.1 cython=3.0.0 dill=0.3.7 pandas=1.4.4 photutils=1.4.0 astroquery=0.4.6 #h5py=3.9.0 pytables jupyterlab gitpython reproject
    conda install h5py=3.9.0
    pip install pyregion==2.1.1 --no-deps
    pip install gvar==10 --no-deps
    pip install lsqfit==13.0.4 --no-deps
    pip install fpdf==1.7.2 --no-deps

Packages necessary for ORBS:

    conda install -n $envname -c conda-forge clint=0.5.1 html2text distro=1.8.0 lxml=4.9.1 python-magic
    pip install gitdb==4.0.7 --no-deps
    pip install smmap==4.0.0 --no-deps
    pip install cadcdata --no-deps
    pip install cadcutils --no-deps

No additional packages are necessary for ORCS.

You may have to install some dependencies such as build-essential for gvar or cfitsio. For Ubuntu users, it can be done doing the following:

    sudo apt install build-essential
    sudo apt install libcfitsio5 libcfitsio-bin

Once this is done, you need to download the software from git.

    mkdir ~/$python_folder
    cd ~/$python_folder
    git clone https://gitlab.cfht.hawaii.edu/astro/sitelle-data-analysis.git

The some setups have to be done for the three packages ORB, ORBS and ORCS:

    cd ~/$python_folder/sitelle-data-analysis/src/orb
    python setup.py build_ext --inplace
    echo $HOME/$python_folder/sitelle-data-analysis/src/orb > ~/miniconda3/envs/$envname/lib/python3.9/site-packages/conda.pth
    echo $HOME/$python_folder/sitelle-data-analysis/src/orbs >> ~/miniconda3/envs/$envname/lib/python3.9/site-packages/conda.pth

The following tests can then be performed:

    python -c 'import orb.core'
    python -c 'import orbs.core'
    python -c 'import orcs.core'
