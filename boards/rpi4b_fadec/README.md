# Pi FADEC

## Patch PREEMPT_RT kernel
The following commands are run on the Raspberry Pi itself. Install git:\
`sudo apt install git`

Clone the Raspberry Pi linux kernel repository.\
`git clone --depth=1 https://github.com/raspberrypi/linux`

Install the tools necessary to build the kernel.\
`sudo apt install bc bison flex libssl-dev make libncurses-dev`

Determine the Raspberry Pi model, i.e. 4/5 64bit and select the correct architecture.
```
# RASPBERRY PI 4B 64bit
cd linux
KERNEL=kernel8
make bcm2711_defconfig
```

```
# RASPBERRY PI 5 64bit
cd linux
KERNEL=kernel_2712
make bcm2712_defconfig
```

Now run the config tool, this should bring up a temrinal GUI.\
``make menuconfig``

Bring up the search bar using `//` and search `PREEMPT_RT`.
Select `(1)`.\
Select `Preemption Model`.\
Select `Fully Preemptable Kernel (Real Time)`.\
Select `<Save>` and write to `.config`.\

You can now build the kernel!
```
make -j6 Image.gz modules dtbs
```

```
sudo env PATH=$PATH make -j12 ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- INSTALL_MOD_PATH=mnt/root modules_install
```