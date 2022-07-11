% load data_1N0U1.mat
% figure; imagesc(pattern)
 
b1 = readNPY('pat_mask.npy');
figure; imagesc(b1)

fid = fopen('pattern.bin', 'r');
data = fread(fid, '*int8');
data2 = fread(fid,[123 123], '*int16');

fclose(fid);

mm=reshape(data,[246 246]);
