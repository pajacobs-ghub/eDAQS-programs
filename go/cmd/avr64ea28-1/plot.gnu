# plot.gnu
# Display the sampled data with Gnuplot by running with the command:
# $ gnuplot -persist < plot.gnu
set datafile separator ','
plot 'node-2.csv' using 1, 'node-2.csv' using 2

