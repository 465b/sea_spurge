# README

The draft  of main file to run is ./sea_spurge/run_ot_for_sea_spurge_AUtoNZ.py  
You'll have to edit it to 
* change the paths to fetch the hindcast data in your environment, I don't know how you plan on doing this exactly,
* and to schedule and batch it so it fits into the cluster interface that you are using.

## how to:
```
git clone https://github.com/465b/sea_spurge.git
cd sea_spurge
mamba create -n seapurge_cluster python=3.13 pip
mamba activate seaspurge_cluster
pip install oceantracker shapely
python ./run_ot_for_sea_spurge_AUtoNZ.py
```