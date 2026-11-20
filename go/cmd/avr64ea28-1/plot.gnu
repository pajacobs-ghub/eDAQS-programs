# plot.gnu
# Display the sampled data with Gnuplot by running with the command:
# $ gnuplot -persist < plot.gnu
set datafile separator ','
plot 'node-1.csv' using 1 with lines, 'node-1.csv' using 2 with lines

