from extra_refine import Extra_refiner

if __name__ == '__main__':
    
    refiner = Extra_refiner()
    # refiner.change_format(4, 5, downgrade_spk=True, downgrade_utt=False)
    refiner.reorder_files()