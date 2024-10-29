"""
OT-2 High-throughput Proxy Viscometer Protocol
New base protocol to collect data

Author: AMDM Group @ IMRE, A STAR
Date: October 2022
"""


from opentrons import protocol_api


metadata = {'apiLevel': '2.10'}     # Opentrons Python API Version


def run(protocol: protocol_api.ProtocolContext):

    reservoir = protocol.load_labware('amdm_12_50ml_falcon_tube', 1)  # custom labware uploaded to the application
    
    # Compatible with Opentrons Application v5.X; for latest v6.X and higher, the labware file should be directly uploaded into the application.
    # falcon tube holder custom labware definition - json file generated using Opentrons' custom labware creator: https://labware.opentrons.com/create/
    # .stl file for 3d-printing this holder provided in the SI
    # 2nd argument denotes position on the Opentrons plate
    
    plate = protocol.load_labware('amdm_6_15g_plasticjars', 2)          # Corning 6-well plate
    plate.set_offset(x=1.00, y=-6.00, z=0.00)                           # Apply Lab offset data
    
    tiprack_1 = protocol.load_labware('opentrons_96_filtertiprack_1000ul', 3)       # Thermo Scientific 1000 uL wide bore tips
    tiprack_1.set_offset(x=-0.20, y=2.30, z=5.00)                                   # Apply Lab offset data
    
    p1000 = protocol.load_instrument('p1000_single_gen2', 'left', tip_racks=[tiprack_1])
    # https://docs.opentrons.com/v2/pipettes/characteristics.html#ot-2-pipette-flow-rates - default flow rate of P1000 gen 2 pipette = 274.7 uL/s

    fr_arr            = [80]  # dispense flowrate/uL/s 
    samples_ran       = 0     # initialization counter
    no_of_samples     = 1
    adepth            = 0     # initialization - will account for what depth to aspirate from depending on past history of volume dispensed
    depth             = -80   # 80 mm from top corresponds to ~ 12.5 mL: fill the reservoir tubes to approx. 20 mL
    asptime           = 10  # protocol aspiration time 
    disptime          = 10    # protocol dispense time
    asp_with = 5
    
    i = 0  # init loop counter

    # Location of stored liquids & destinations
    res_letter_list = ["A", "C"]
    well_letter_list = ["A", "B"]
                                                             
    while samples_ran < no_of_samples: 
        if i == 0:
            p1000.pick_up_tip(tiprack_1["A" + str(samples_ran+1)])   # pick up pipette tip

        # Handling of viscous fluids
        for e in range(1):  # triplicate measurements
            # aspirate liquid
            depth -= adepth
            p1000.aspirate((fr_arr[i]*asptime), reservoir[str(res_letter_list[samples_ran])+"1"].top(z=depth), rate=100/274.7) 
            protocol.delay(seconds=30)
            p1000.default_speed = 100
            p1000.move_to(reservoir[str(res_letter_list[samples_ran])+"1"].top(z=-2), speed=asp_with)

            for e in range(2):  # touch tip x 2 @ -10 mm from top, x 1 @ -1 mm from top, x1 @ top
                p1000.touch_tip(radius=1, v_offset=-10)
            p1000.touch_tip(radius=1, v_offset=-6)
            p1000.touch_tip(radius=1.2, v_offset=-3)
        
            # dispense liquid
            p1000.dispense((fr_arr[i]*disptime), plate[str(well_letter_list[samples_ran]) + "1"].top(10), rate=float(fr_arr[i]/274.7))
            protocol.delay(seconds=30)
        
            # getting rid of excess liquid
            p1000.dispense(1000, reservoir[str(res_letter_list[samples_ran])+"1"].top(), rate=100/274.7)
            protocol.delay(seconds=20)
            p1000.aspirate(400, reservoir[str(res_letter_list[samples_ran])+"1"].top(), rate=100/274.7)
            protocol.delay(seconds=10)
            p1000.dispense(400, reservoir[str(res_letter_list[samples_ran])+"1"].top(), rate=100/274.7)
            p1000.touch_tip(v_offset=-10)
            p1000.default_speed = 400
            for e in range(10): # number of tip blowouts 
                p1000.blow_out(reservoir[str(res_letter_list[samples_ran])+"1"])
            
            # add 1mm of depth for every 10000/9ul aspirated from falcon tube
            tdisp = (fr_arr[i]*disptime)/ 1000.0
            adepth = tdisp * (9/5)  # 5ml is 9mm
        
        i += 1  # useful if you wish to test multiple flow rates

        if i == len(fr_arr):
            for e in range(10):
                p1000.blow_out(reservoir[str(res_letter_list[samples_ran])+"1"])
            p1000.drop_tip()
            
        samples_ran += 1
        depth = -80     
