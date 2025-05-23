This release of ORB/ORBS/ORCS is from the version provided by Thomas Martin (https://github.com/thomasorb) at the date of April 1st 2024.

The intent of this package is to have a fully workable version of ORCS. ORBS has not been tested and may not be necessary. Nevertheless, this package may be merged in the future with the software suite used at CFHT to perform the reduction of SITELLE data with ORBS, so that one single package enables to reduce and analyse the data.

In order to install the package properly, an environment has to be set. We have compiled all versions of packages that enable the software to run properly.

One can define an environment name (conda environment) and specify the repository where it will be installed in the user home directory ($HOME):

    envname='orb3'
    python_folder='python_programs'

First, it is necessary to install Miniconda to create the proper python environment with the appropriate package versions:

    mkdir -p $HOME/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $HOME/miniconda3/miniconda.sh
    bash $HOME/miniconda3/miniconda.sh -b -u -p $HOME/miniconda3
    rm -rf $HOME/miniconda3/miniconda.sh
    $HOME/miniconda3/bin/conda init bash
    . .bashrc

The environment can then be created and activated:

    conda create -n $envname --yes
    conda activate $envname

Once this is done, it is time to install the required python packages.

Packages necessary for ORB:

    conda install --yes -c conda-forge -c astropy -c anaconda python=3.9.7 ipython astropy=5.3.4 numpy=1.24.3 scipy=1.10.1 matplotlib=3.5.1 cython=3.0.0 dill=0.3.7 pandas=1.4.4 photutils=1.4.0 astroquery=0.4.6 pytables jupyterlab gitpython reproject
    conda install --yes h5py=3.9.0
    pip install pyregion==2.2.0 --no-deps  # the version that was previously used does not install properly anymore with the latest conda version: pip install pyregion==2.1.1 --no-deps
    pip install gvar==10 --no-deps
    pip install lsqfit==13.0.4 --no-deps
    pip install fpdf==1.7.2 --no-deps

Packages necessary for ORBS:

    conda install --yes -c conda-forge clint=0.5.1 html2text distro=1.8.0 lxml=4.9.1 python-magic
    pip install gitdb==4.0.7 --no-deps
    pip install smmap==4.0.0 --no-deps
    pip install cadcdata --no-deps
    pip install cadcutils --no-deps

No additional packages are necessary for ORCS.

You may have to install some dependencies such as build-essential for gvar or cfitsio. For Ubuntu users, it can be done doing the following:

    sudo apt install build-essential
    sudo apt install libcfitsio5 libcfitsio-bin

Once this is done, you need to download the software from git:

    mkdir $HOME/$python_folder
    cd $HOME/$python_folder
    git clone https://github.com/bepinat/sitelle-data-analysis.git

Some setups have to be done for the three packages ORB, ORBS and ORCS:

    cd $HOME/$python_folder/sitelle-data-analysis/src/orb
    python setup.py build_ext --inplace
    echo $HOME/$python_folder/sitelle-data-analysis/src/orb > $HOME/miniconda3/envs/$envname/lib/python3.9/site-packages/conda.pth  # for developers
    python setup.py install  # not for developer

    cd $HOME/$python_folder/sitelle-data-analysis/src/orbs
    echo $HOME/$python_folder/sitelle-data-analysis/src/orbs >> $HOME/miniconda3/envs/$envname/lib/python3.9/site-packages/conda.pth  # for developers
    python setup.py install  # not for developer

    cd $HOME/$python_folder/sitelle-data-analysis/src/orcs
    python setup.py install

The following tests can then be performed:

    python -c 'import orb.core'
    python -c 'import orbs.core'
    python -c 'import orcs.core'

Then, for developpers, scripts (orb-convert, orbs, orbs-fit-calibration-laser-map, orbs-sitelle-makejob) may be linked to the binaries of the environment:

    ln -s $HOME/$python_folder/sitelle-data-analysis/src/orb/scripts/orb-convert $HOME/miniconda3/envs/$envname/bin/
    ln -s $HOME/$python_folder/sitelle-data-analysis/src/orbs/scripts/orbs $HOME/miniconda3/envs/$envname/bin/
    ln -s $HOME/$python_folder/sitelle-data-analysis/src/orbs/scripts/orbs-fit-calibration-laser-map $HOME/miniconda3/envs/$envname/bin/
    ln -s $HOME/$python_folder/sitelle-data-analysis/src/orbs/scripts/orbs-sitelle-makejob $HOME/miniconda3/envs/$envname/bin/

They can alternatively be put in the user $PATH (this can be added in the .bashrc), but this will also be effective outside the environment:

    export PATH=$PATH:$HOME/$python_folder/sitelle-data-analysis/src/orb/scripts:$HOME/$python_folder/sitelle-data-analysis/src/orbs/scripts  # for developers
