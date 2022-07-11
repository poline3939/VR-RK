from spipy.phase import phase2d
import sys

if __name__=="__main__":

	params_essential = {'input|shape' : '123,123', 'input|padd_to_pow2' : True, \
		'input|inner_mask' : 5, 'input|outer_mask' : 64, \
		'input|outer_outer_mask' : None, 'input|mask_edges' : True, \
		'phasing|repeats' : 1, 'phasing|iters' : '200RAAR 200DM 200ERA', \
		'phasing_parameters|support_size' : 100, 'phasing_parameters|beta' : 0.8}
	params_optional = {'input|subtract_percentile' : None, 'input|spherical_support' : None, \
		'phasing_parameters|background' : 'True', 'input|init_model' : None}

	print("\nCreate new project ...")
	phase2d.new_project(data_mask_path=['pattern.bin','pat_mask.npy'], path='./', name=None)

	print("\nConfiguring ...")
	parameters = dict(params_essential, **params_optional)
	phase2d.config(params = parameters)

	print("\nStart ! Run in background ! Check log file for details!")
	phase2d.run(num_proc=1, nohup=False, cluster=True)

	print("\nRun ' python show_result.py output.h5 ' at the project dir to see results.\n")
	sys.exit(0)
	phase2d.show_result(outpath=None, exp_param='581,7.9,128,0.3')
