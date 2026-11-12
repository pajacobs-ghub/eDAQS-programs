# plot.gnu
# Display the sampled data with Gnuplot by running with the command:
# $ gnuplot -persist < plot.gnu
set datafile separator ','
plot 'node-G.csv' using 1, 'node-G.csv' using 12, 'node-G.csv' using 13
