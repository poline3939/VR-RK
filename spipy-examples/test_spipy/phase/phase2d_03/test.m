% show results
% numpy, f is the function handle
% d: f['data'], data (input data)
% input
d1=h5read('output.h5','/data');
d1_1=fftshift(d1);
d1_2=abs(d1_1);
d2=log(1+d1_1);
d2_2=log(1+d1_2);
figure; imagesc(d2)
figure; imagesc(d2_2)

%output
t1=h5read('output.h5','/data retrieved');
t1_1=fftshift(t1);
t2=log(1+t1_1);
figure; imagesc(t2)

h5disp('output.h5')

% others: output data in the real space 
h1=h5read('output.h5','/sample retrieved');
h1_1=fftshift(h1.r);
h2=log(1+h1_1);
figure; imagesc(h1_1)
