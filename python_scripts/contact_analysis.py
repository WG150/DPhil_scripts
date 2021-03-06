""" This script calculates the contacts between protein monomers and returns a contact map for each interface."""

import seaborn
import MDAnalysis as mda
import numpy as np
from MDAnalysis.lib.distances import distance_array  # faster C lib
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm as CM
from matplotlib import rcParams

rcParams.update({'figure.autolayout': True})
import seaborn as sns
import pandas as pd
import glob, os
from os.path import join
from datetime import datetime
import argparse

__author__ = "William Glass"
__email__ = "william.glass@chem.ox.ac.uk"

print ' '
print "### Modules Used ####"
print ' '
print "NumPy Version: " + np.__version__
print "MDAnalysis Version: " + mda.__version__
print "Matplotlib Version: " + matplotlib.__version__
print ' '
print "#####################"
print ' '

# Define constants and libraries

# TODO generalise this for N monomers, mixed proteins & lipid contacts.
num_protein = 3

lipid_head_group_dict = {'popc': 'PO4', 'pope': 'NH3', 'dpsm': 'NC3', 'dpg3': 'GM1', 'chol': 'ROH', 'pops': 'CN0',
                         'pop2': 'P1'}
lipid_group_dict = {'popc': 'POPC', 'pope': 'POPE', 'dpsm': 'DPSM', 'dpg3': 'DPG3', 'chol': 'CHOL', 'pops': 'POPS',
                    'pop2': 'POP2'}

# TODO would be interesting to use just the side chain atoms of interest to calc the centre of mass from in the future
residue_side_chains = {}


# def protein_lipid_interactions(coord, traj):
#     u = mda.Universe(coord, traj)
#
#     resid_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resids)  # convert list to array
#     atom_list = np.asarray(u.select_atoms("protein").positions)
#
#     resname_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resnames)


class Heatmap(object):

    def __init__(self, u, method="residue", cut_off=4.0):

        """Return a heatmap object"""

        self.u = u
        self.method = method
        self.cut_off = cut_off


        if method == 'residue':
            self.resid_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resids)#list to array
            self.heatmap = np.zeros((len(self.resid_list), len(self.resid_list)))
        elif method == 'atom':
            self.atom_list = np.asarray(u.select_atoms("protein").positions)
            self.heatmap = np.zeros((len(self.atom_list), len(self.atom_list)))

    def populate_hmap_single_frame(self):
        """
        populates empty heatmap array for a single frame

        """

        if self.method == "residue":

            cog_store = np.zeros((len(self.resid_list), 3))

            N = len(self.resid_list)  # pre-allocate to speed up calc

            # can we speed this up?!
            for residue in range(len(self.resid_list)):  # For each residue, calculate the c.o.g and store

                cog_store[residue] = self.u.select_atoms("resid " + str(self.resid_list[residue])).center_of_geometry()

            # Calculate a distance matrix

            d = distance_array(np.array(cog_store).astype(np.float32), np.array(cog_store).astype(np.float32),
                               box=self.u.dimensions, result=np.empty(shape=(N, N), dtype=np.float64),
                               backend='OpenMP')

        elif self.method == "atom":

            N = len(self.atom_list)  # pre-allocate to speed up calc

            d = distance_array(np.array(self.atom_list).astype(np.float32), np.array(self.atom_list).astype(np.float32),
                               box=self.u.dimensions, result=np.empty(shape=(N, N), dtype=np.float64),
                               backend='OpenMP')

        # Define a new heat map based on a user defined cut-off and convert to 1's & 0's

        self.heatmap += (d < self.cut_off).astype(int)

        #return self.heatmap


    # def make_hmap(self, coord, traj):
    #     u = mda.Universe(coord, traj)
    #
    #     """
    #     makes an empty numpy array to be populated.
    #     coord = a GROMACS .gro file
    #     traj = a GROMACS .xtc file
    #
    #     """
    #
    #     if options.region == 'all':
    #
    #         resid_list = np.asarray(
    #             u.select_atoms("protein and not backbone").atoms.residues.resids)  # convert list to array
    #
    #         atom_list = np.asarray(u.select_atoms("protein").positions)
    #
    #         resname_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resnames)
    #
    #     elif options.region == 'specific':
    #
    #         # resid_list = np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490) and not backbone").atoms.residues.resids) # convert list to array
    #         # atom_list = np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490)").positions)
    #         #
    #         #
    #         # resname_list = np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490) and not backbone").atoms.residues.resnames)
    #
    #         resid_list = np.asarray(
    #             u.select_atoms(str(options.selection) + " and not backbone").atoms.residues.resids)  # convert list to array
    #
    #         atom_list = np.asarray(u.select_atoms(str(options.selection)).positions)
    #
    #         resname_list = np.asarray(u.select_atoms(str(options.selection) + " and not backbone").atoms.residues.resnames)
    #
    #     residue_heat_map = np.zeros((len(resid_list), len(resid_list)))  # define the array size before making the heatmap
    #
    #     atom_heat_map = np.zeros((len(atom_list), len(atom_list)))
    #
    #     return resid_list, atom_list, residue_heat_map, atom_heat_map, u, resname_list









def plot_hmap(data, residues, atoms, cut_off):
    """plot a single frame
    data = the populated hmap
    names = list of amino acid names
    resids = list of resids of amino acids
    """
    print "Making plot..."

    data = (data / np.amax(data)) * 100  # normalise to make a percentage

    # mask = np.tri(data.shape[0], k=-1)
    # A = np.ma.array(data, mask=mask)  # mask out the lower triangle

    fig = plt.figure()

    ax = fig.add_subplot(111)

    # colors = cm.ScalarMappable(cmap="viridis").to_rgba(data_value)

    # surf = ax.plot_surface(x,y,z,rstride=1, cstride=1,linewidth=0, antialiased=True)

    plt.title('Interaction Map of Contacts < ' + str(cut_off) + ' $\AA$', y=1.08)

    cmap = CM.get_cmap('viridis', 10)  # jet doesn't have white color

    cmap.set_bad('w')  # default value is 'k'

    plt.imshow(data, cmap='viridis', interpolation='bicubic')
    ax.grid(False)

    if options.plot_type == "residue":

        # Add lines to see where protein repeats start and stop
        ax.axvline((len(residues) / num_protein), c='white', linestyle='--', lw=0.4)
        ax.axvline((len(residues) / num_protein) * (num_protein - 1), c='white', linestyle='--', lw=0.4)
        ax.axhline((len(residues) / num_protein), c='white', linestyle='--', lw=0.4)
        ax.axhline((len(residues) / num_protein) * (num_protein - 1), c='white', linestyle='--', lw=0.4)

        plt.xlabel("Residue Number")
        plt.ylabel("Residue Number")

        ## Annotate the chains...

        ax.xaxis.set_tick_params(labeltop='on')

        cent1 = ((len(residues) / num_protein) / 2)
        cent2 = cent1 + (2 * cent1)
        cent3 = cent1 + (4 * cent1)

        # ann = ax.annotate('A', xy=(83, 83), xytext=(83, 83), xycoords='data',
        #             fontsize=12, ha='center', va='bottom',
        #             bbox=dict(boxstyle='square', fc='white'))
        #
        # ann2 = ax.annotate('B', xy=(249, 249), xytext=(249, 249), xycoords='data',
        #                   fontsize=12, ha='center', va='bottom',
        #                   bbox=dict(boxstyle='square', fc='white'))
        #
        # ann3 = ax.annotate('C', xy=(415, 415), xytext=(415, 415), xycoords='data',
        #                   fontsize=12, ha='center', va='bottom',
        #                   bbox=dict(boxstyle='square', fc='white'))

        ann = ax.annotate('A', xy=(cent1, cent1), xytext=(cent1, cent1), xycoords='data',
                          fontsize=12, ha='center', va='bottom',
                          bbox=dict(boxstyle='square', fc='white'))

        ann2 = ax.annotate('B', xy=(cent2, cent2), xytext=(cent2, cent2), xycoords='data',
                           fontsize=12, ha='center', va='bottom',
                           bbox=dict(boxstyle='square', fc='white'))

        ann3 = ax.annotate('C', xy=(cent3, cent3), xytext=(cent3, cent3), xycoords='data',
                           fontsize=12, ha='center', va='bottom',
                           bbox=dict(boxstyle='square', fc='white'))

    elif options.plot_type == "atom":

        # Add lines to see where protein repeats start and stop
        ax.axvline((len(atoms) / num_protein), c='white', linestyle='--', lw=0.4)
        ax.axvline((len(atoms) / num_protein) * (num_protein - 1), c='white', linestyle='--', lw=0.4)
        ax.axhline((len(atoms) / num_protein), c='white', linestyle='--', lw=0.4)
        ax.axhline((len(atoms) / num_protein) * (num_protein - 1), c='white', linestyle='--', lw=0.4)

        plt.xlabel("Atom Index")
        plt.ylabel("Atom Index")

        cent1 = ((len(atoms) / num_protein) / 2)
        cent2 = cent1 + (2 * cent1)
        cent3 = cent1 + (4 * cent1)

        ## Annotate the chains...

        ax.xaxis.set_tick_params(labeltop='on')

        ann = ax.annotate('A', xy=(cent1, cent1), xytext=(cent1, cent1), xycoords='data',
                          fontsize=12, ha='center', va='bottom',
                          bbox=dict(boxstyle='square', fc='white'))

        ann2 = ax.annotate('B', xy=(cent2, cent2), xytext=(cent2, cent2), xycoords='data',
                           fontsize=12, ha='center', va='bottom',
                           bbox=dict(boxstyle='square', fc='white'))

        ann3 = ax.annotate('C', xy=(cent3, cent3), xytext=(cent3, cent3), xycoords='data',
                           fontsize=12, ha='center', va='bottom',
                           bbox=dict(boxstyle='square', fc='white'))

    cbar = plt.colorbar()
    cbar.ax.set_ylabel('Average of Interaction (%)', rotation=270)
    cbar.ax.get_yaxis().labelpad = 20

    return fig


def plot_sub_plots(data, residues, atoms, cut_off, residue_names):
    # This function currently only works for num proteins = 3, would be good to generalise this to any number soon.

    N = int(len(residues))

    print "Making subplots..."

    '''plot a single frame
    data = the populated hmap
    names = list of amino acid names
    resids = list of resids of amino acids
    '''

    data = (data / np.amax(data)) * 100  # normalise to make a percentage

    # Get interaction columns
    ints_on_a = data[0:(N / num_protein), 0:(3 * (N / num_protein))]
    ints_on_b = data[N / num_protein:(2 * (N / num_protein)), 0:(3 * (N / num_protein))]
    ints_on_c = data[2 * (N / num_protein):(3 * (N / num_protein)), 0:(3 * (N / num_protein))]

    print(ints_on_a)
    print(ints_on_b)
    print(ints_on_c)

    # sum_ints_on_a = np.sum(ints_on_a, axis=1) / 100
    # sum_ints_on_b = np.sum(ints_on_b, axis=1) / 100
    # sum_ints_on_c = np.sum(ints_on_c, axis=1) / 100

    # Sum (down columns) all of the interactions on each protein. You need to minus the contribution made from the
    # protein contacts made with itself so you are then left with the interactions made with other proteins in the
    # system.

    sum_ints_on_a = (np.sum(ints_on_a, axis=1) - np.sum(data[0:(N / num_protein), 0:(N / num_protein)],
                                                        axis=1))
    sum_ints_on_b = (np.sum(ints_on_b, axis=1) - np.sum(
        data[N / num_protein:(2 * (N / num_protein)), N / num_protein:(2 * (N / num_protein))],
        axis=1))
    sum_ints_on_c = (np.sum(ints_on_c, axis=1) - np.sum(
        data[2 * (N / num_protein):(3 * (N / num_protein)), 2 * (N / num_protein):(3 * (N / num_protein))],
        axis=1))

    # Normalise interactions on each chain
    sum_ints_on_a = (sum_ints_on_a / np.amax(sum_ints_on_a)) * 100
    sum_ints_on_b = (sum_ints_on_b / np.amax(sum_ints_on_b)) * 100
    sum_ints_on_c = (sum_ints_on_c / np.amax(sum_ints_on_c)) * 100

    fig = plt.figure()

    ax = fig.add_subplot(111)

    # make xlabels (the resids) and +1 due to 0 index.

    x = [i + 1 for i in range(len(sum_ints_on_a))]

    ax.bar(x, sum_ints_on_a, label='Chain A')
    ax.bar(x, sum_ints_on_b, label='Chain B')
    ax.bar(x, sum_ints_on_c, label='Chain C')

    ax.set_xlabel('Intermolecular Interaction (%)')
    ax.set_ylabel('Residue Number')

    plt.legend()

    plt.savefig('bar.svg', format='svg', dpi=300)

    plt.show()


    data_1_2 = data[0:(N / num_protein),
               (N / num_protein):(2 * (N / num_protein))]  # Protein A interacting with Protein B
    data_1_3 = data[0:(N / num_protein),
               (2 * (N / num_protein)):(3 * (N / num_protein))]  # Protein A interacting with Protein C
    data_2_3 = data[(N / num_protein):(2 * (N / num_protein)),
               (2 * (N / num_protein)):(3 * (N / num_protein))]  # Protein B interacting with Protein C

    sub_plot_data_list = [data_1_2, data_1_3, data_2_3]

    for i in range(len(sub_plot_data_list)):

        if i == 0:

            xlab = "Protein B"
            ylab = "Protein A"
            focus = "AB"

        elif i == 1:

            xlab = "Protein C"
            ylab = "Protein A"
            focus = "AC"

        elif i == 2:

            xlab = "Protein C"
            ylab = "Protein B"
            focus = "BC"

        sub_fig = plt.figure()

        ax = sub_fig.add_subplot(111)

        if options.plot_type == "residue":

            plt.xlabel("Residue Number (" + str(xlab) + ")")
            plt.ylabel("Residue Number (" + str(ylab) + ")")

            ax.grid(linestyle='--', linewidth=1)
            ax.xaxis.set_tick_params(labeltop='on')

            plt.title('Interaction Map of Contacts < ' + str(cut_off) + ' $\AA$', y=1.08)

            plt.imshow(sub_plot_data_list[i], cmap='viridis', interpolation='bicubic')

            cbar = plt.colorbar()
            cbar.ax.set_ylabel('Average of Interaction (%)', rotation=270)
            cbar.ax.get_yaxis().labelpad = 20

            sub_fig.savefig('sub_figure_' + str(options.plot_type) + str(i) + '.svg', format='svg')

            sub_fig.clf()

            #### bar chart plot ####


            bar_data_0 = np.sum(sub_plot_data_list[i],
                                axis=0) / 100  # Calculate sum of interactions for protein on x axis of heat map
            bar_data_1 = np.sum(sub_plot_data_list[i],
                                axis=1) / 100  # Calculate sum of interactions for protein on y axis of heat map

            bar_data_0_30 = bar_data_0[(bar_data_0 >= 30)]  # filter out values only higher than 30 %
            bar_data_1_30 = bar_data_1[(bar_data_1 >= 30)]  # filter out values only higher than 30 %

            resid_x0_labs = (
            np.where(bar_data_0 >= 30))  # Get the resid's of the residues in contact >= 30% of the time
            resid_x1_labs = (
            np.where(bar_data_1 >= 30))  # Get the resid's of the residues in contact >= 30% of the time

            resid_x0_labs = list(resid_x0_labs[0])  # Need to convert to a list for later
            resid_x1_labs = list(resid_x1_labs[0])

            # print resid_x1_labs

            # print residue_names[0:(N/3)]

            ### sorting out axis labels ###

            resname_x0_labs = [residue_names[0:(N / 3)][k - 1] for k in resid_x0_labs]  # extract the correct names

            resname_x1_labs = [residue_names[0:(N / 3)][k - 1] for k in resid_x1_labs]

            resname_resnum_x0_labs = ([m + str(n) for m, n in zip(list(resname_x0_labs),
                                                                  resid_x0_labs)])  # combine the names and the resid number

            resname_resnum_x1_labs = ([m + str(n) for m, n in zip(list(resname_x1_labs), resid_x1_labs)])

            # print resname_resnum_x1_labs

            ### Begin plotting ####

            for j in range(2):  # need to know if summed over rows or down columns of each sub heatmap plot...

                print ("j = " + str(j))

                sub_bar_fig = plt.figure()

                ax = sub_bar_fig.add_subplot(111)

                if j == 0:  # we are looking at the sum down columns

                    # plt.xticks(range(len(resid_x0_labs[0])), list(resid_x0_labs[0]))

                    plt.xticks(range(len(resname_resnum_x0_labs)), list(resname_resnum_x0_labs), rotation='vertical')

                    plt.title(str(ylab) + ' vs. ' + str(xlab) + ': Interaction of Contacts < ' + str(
                        cut_off) + ' $\AA$ (.ge. 30%)', y=1.08)

                    plt.xlabel("Residue Number " + str(xlab))
                    plt.ylabel("Interaction (%)")

                    plt.bar(range(len(bar_data_0_30)), bar_data_0_30)

                elif j == 1:  # we are looking at the sum across rows

                    # plt.xticks(range(len(resid_x1_labs[0])), list(resid_x1_labs[0]))

                    plt.xticks(range(len(resname_resnum_x1_labs)), list(resname_resnum_x1_labs), rotation='vertical')

                    plt.title(str(ylab) + ' vs. ' + str(xlab) + ': Interaction of Contacts < ' + str(
                        cut_off) + ' $\AA$ (.ge. 30%)', y=1.08)

                    plt.xlabel("Residue Number of " + str(ylab))
                    plt.ylabel("Interaction (%)")

                    plt.bar(range(len(bar_data_1_30)), bar_data_1_30)

                sub_bar_fig.savefig('sub_bar_figure_' + str(options.plot_type) + str(focus) + str(j) + '.svg',
                                    format='svg')


def assign_beta_values(universe, residue_ids):  #### STILL IN TEST PHASE ####

    """

    Takes the universe supplied and colours the resides based on their contact map vlaue. Two options can be used.

    1) "residue": this colours each residue according to if their COM is within the defined cut off (faster)
    2) "atom": this colours each atom according to if their COM is within the defined cut off (slower)

    """

    print "Writing contacts to PDB file..."

    u.trajectory[-1]  # reset the trajectory to the final frame prior to writing the beta values

    protein_atom_selection = u.select_atoms("protein")

    # protein_residue_selection = u.select_atoms("resid 1:" + str(len(residue_ids)))  # TO FIX!!!!!

    # protein_residue_selection = u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490) and not backbone")

    protein_residue_selection = u.select_atoms("protein")

    if options.plot_type == "residue":

        residues_per_protein = (len(residue_ids) / num_protein)

        prot_1_2_array = heat_map_pop[0:(residues_per_protein), (residues_per_protein):((residues_per_protein) * 2)]

        prot_1_3_array = heat_map_pop[0:(residues_per_protein), (residues_per_protein * 2):(residues_per_protein * 3)]

        prot_2_3_array = heat_map_pop[(residues_per_protein):((residues_per_protein) * 2),
                         (residues_per_protein * 2):(residues_per_protein * 3)]

        # temporary fix (from MDAnalysis site: https://www.mdanalysis.org/MDAnalysisTutorial/writing.html)
        u.add_TopologyAttr(mda.core.topologyattrs.Tempfactors(np.zeros(len(u.atoms))))

        cat_arrays = np.concatenate([prot_1_2_array.mean(0), prot_2_3_array.mean(0), prot_1_3_array.mean(0)])

    elif options.plot_type == "atom":

        atoms_per_protein = (len(universe.select_atoms("protein").positions) / num_protein)

        prot_1_2_array = heat_map_pop[0:(atoms_per_protein), (atoms_per_protein):((atoms_per_protein) * 2)]

        prot_1_3_array = heat_map_pop[0:(atoms_per_protein), (atoms_per_protein * 2):(atoms_per_protein * 3)]

        prot_2_3_array = heat_map_pop[(atoms_per_protein):((atoms_per_protein) * 2),
                         (atoms_per_protein * 2):(atoms_per_protein * 3)]

        # temporary fix (from MDAnalysis site: https://www.mdanalysis.org/MDAnalysisTutorial/writing.html)
        u.add_TopologyAttr(mda.core.topologyattrs.Tempfactors(np.zeros(len(u.atoms))))

        cat_arrays = np.concatenate([prot_1_2_array.mean(0), prot_2_3_array.mean(0), prot_1_3_array.mean(0)])

    if options.plot_type == "residue":

        # beta_residue_array = np.zeros((len(np.asarray(u.select_atoms("protein").positions)), 1))

        beta_residue_array = np.zeros((len(np.asarray(u.select_atoms("protein").positions))))

        # beta_residue_array = np.zeros((len(np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490)").positions)), 1))

        print residue_ids

        for i in range(len(residue_ids)):

            ##### SPECIFIC #####

            if options.region == "specific":

                residue_coords = u.select_atoms("resid " + str(residue_ids[i])).positions

                residue_coords_corrected = []

                for j in range(len(residue_coords)):
                    residue_coords_corrected.append(range(np.size(residue_coords))[j] +
                                                    u.select_atoms("resid " + str(residue_ids[i])).atoms.indices[0])

                beta_residue_array[residue_coords_corrected] = cat_arrays[i]

            #### GENERAL #####

            if options.region == "all":

                residue_coords = u.select_atoms("resid " + str(i + 1)).positions  # select every atom of a residue

                if i == 0:

                    beta_residue_array[[range(np.size(residue_coords))]] = cat_arrays[i]

                    prev_indices = range(np.size(residue_coords, 0))

                    index_max = np.max(
                        prev_indices)  # store the max index number in the first instance. +1 due to 0-indexing

                elif i > 0:

                    current_indices = range(np.size(residue_coords, 0))

                    new_current_indices = [x + (index_max + 1) for x in current_indices]  # updating the number...

                    beta_residue_array[[new_current_indices]] = cat_arrays[i]

                    # for next loop...

                    # current_indices = new_current_indices

                    index_max += (np.max(range(np.size(residue_coords, 0))) + 1)

        protein_residue_selection.tempfactors = beta_residue_array

        protein_residue_selection.write("residue_bfact.pdb", format("PDB"))

    elif options.plot_type == "atom":

        protein_atom_selection.tempfactors = cat_arrays

        protein_atom_selection.write("atom_bfact.pdb", format("PDB"))

        protein_atom_selection.write()

        # BELOW is commented out since it worked only with older verison of mda (pre 0.17.0)

        # for i, b in enumerate(np.concatenate([prot_atoms_1_2_array.mean(0), prot_atoms_2_3_array.mean(0), prot_atoms_1_3_array.mean(0)])):
        #
        #     protein_selection.select_atoms("bynum " + str(i)).tempfactors = b


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Calculates the contacts between chains")
    parser.add_argument("-c", dest="gro_file", type=str, help='the coordinate file [.gro]')
    parser.add_argument("-f", dest="xtc_file", type=str,
                        help='a corrected trajectory file, pbc artifacts removed and the protein centered')
    parser.add_argument("-d", dest="cut_off_value", type=float, help='the cut-off value')
    parser.add_argument("-p", dest="plot_type", type=str,
                        help="define the heatplot type, i.e residue - residue or atom - atom.")
    parser.add_argument("-region", dest="region", type=str,
                        help="decide to analyse all of the protein or a specific region: 'all' or 'specific'",
                        required=True, default="all")
    parser.add_argument("-sel", dest="selection", type=str,
                        help="if -region flag included, this is the selection string. e.g. resid 1:100")
    parser.add_argument("-skip", dest="skip", type=int, default=0,
                        help="No. of frames to skip, default = 0")

    options = parser.parse_args()

    if options.region == 'specific' and options.selection == None:
        parser.error("-region 'specific' requires -sel flag, make sure you have included the selection!")

    startTime = datetime.now()

    residue_ids, atom_ids, initial_residue_heat_map, initial_atom_heat_map, u, resnames = make_hmap(
        coord=options.gro_file, traj=options.xtc_file)

    for frame in u.trajectory[::options.skip]:

        if u.trajectory.frame % 10 == 0:
            print "Frame = " + str(u.trajectory.frame)

        # if u.trajectory.frame == 2:
        #     break

        u.trajectory[frame.frame]

        if options.plot_type == "residue":

            heat_map_pop = populate_hmap(heatmap=initial_residue_heat_map, universe=u, resid=residue_ids,
                                         cut_off=options.cut_off_value)

        elif options.plot_type == "atom":

            heat_map_pop = populate_hmap(heatmap=initial_atom_heat_map, universe=u, resid=residue_ids,
                                         cut_off=options.cut_off_value)

    # try:
    assign_beta_values(universe=u, residue_ids=residue_ids)
    # except Exception:
    # pass

    identify_residues = heat_map_pop.astype(str)

    # Plot the whole hmap
    fig = plot_hmap(data=heat_map_pop, residues=residue_ids, atoms=atom_ids, cut_off=options.cut_off_value)

    # Plot each heatmap for each protein - proein interaction
    plot_sub_plots(data=heat_map_pop, residues=residue_ids, atoms=atom_ids, cut_off=options.cut_off_value,
                   residue_names=resnames)

    fig.savefig('figure_' + str(options.plot_type) + '.svg', format='svg')
    fig.clf()

    print "Time taken = " + str(datetime.now() - startTime)

























































































#
# """ This script calculates the contacts between protein monomers and returns a contact map for each interface."""
#
# import seaborn
# import MDAnalysis as mda
# import numpy as np
# from MDAnalysis.lib.distances import distance_array # faster C lib
# import matplotlib
# import matplotlib.pyplot as plt
# from matplotlib import cm as CM
# from matplotlib import rcParams
# rcParams.update({'figure.autolayout': True})
# import seaborn as sns
# import pandas as pd
# import glob, os
# from os.path import join
# from datetime import datetime
# import argparse
#
# __author__ = "William Glass"
# __email__ = "william.glass@chem.ox.ac.uk"
#
# print ' '
# print "### Modules Used ####"
# print ' '
# print "NumPy Version: " + np.__version__
# print "MDAnalysis Version: " + mda.__version__
# print "Matplotlib Version: " + matplotlib.__version__
# print ' '
# print "#####################"
# print ' '
#
# # Define constants and libraries
#
# #TODO generalise this for N monomers, mixed proteins & lipid contacts.
# num_protein = 3
#
# lipid_head_group_dict = {'popc' : 'PO4', 'pope' : 'NH3', 'dpsm' : 'NC3', 'dpg3' : 'GM1', 'chol' : 'ROH', 'pops' : 'CN0',
#                          'pop2' : 'P1'}
# lipid_group_dict = {'popc' : 'POPC', 'pope' : 'POPE', 'dpsm' : 'DPSM', 'dpg3' : 'DPG3', 'chol' : 'CHOL', 'pops' : 'POPS',
#                     'pop2' : 'POP2'}
#
# #TODO would be interesting to use just the side chain atoms of interest to calc the centre of mass from in the future
# residue_side_chains = {}
#
# def protein_lipid_interactions(coord, traj):
#
#     u = mda.Universe(coord, traj)
#
#     resid_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resids)  # convert list to array
#     atom_list = np.asarray(u.select_atoms("protein").positions)
#
#     resname_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resnames)
#
# def make_hmap(coord, traj):
#
#     u = mda.Universe(coord, traj)
#
#     """
#     makes an empty numpy array to be populated.
#     coord = a GROMACS .gro file
#     traj = a GROMACS .xtc file
#
#     """
#
#     if options.region == 'all':
#
#         resid_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resids) # convert list to array
#
#         atom_list = np.asarray(u.select_atoms("protein").positions)
#
#         resname_list = np.asarray(u.select_atoms("protein and not backbone").atoms.residues.resnames)
#
#     elif options.region == 'specific':
#
#         # resid_list = np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490) and not backbone").atoms.residues.resids) # convert list to array
#         # atom_list = np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490)").positions)
#         #
#         #
#         # resname_list = np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490) and not backbone").atoms.residues.resnames)
#
#         resid_list = np.asarray(u.select_atoms(str(options.selection) + " and not backbone").atoms.residues.resids) # convert list to array
#
#         atom_list = np.asarray(u.select_atoms(str(options.selection)).positions)
#
#         resname_list = np.asarray(u.select_atoms(str(options.selection) + " and not backbone").atoms.residues.resnames)
#
#     residue_heat_map = np.zeros((len(resid_list), len(resid_list))) # define the array size before making the heatmap
#
#     atom_heat_map = np.zeros((len(atom_list), len(atom_list)))
#
#
#     return resid_list, atom_list, residue_heat_map, atom_heat_map, u, resname_list
#
# def populate_hmap(heatmap, universe, resid, cut_off):
#
#     """populates empty heatmap array for a single frame
#     heatmap = empty numpy array of N x N
#     universe = a single frame or whole trajectory
#     resid = list of residue ids
#     cut_off = the cut-off value set by the user
#     """
#
#     #heat_map_pop = empty_heatmap    # reset for the next cycle
#
#     if options.plot_type == "residue":
#
#         cog_store = np.zeros((len(resid), 3))
#
#         N = len(resid)  # pre-allocate to speed up calc
#
#         # can we speed this up?!
#         for residue in range(len(resid)):  # For each residue, calculate the c.o.g and store
#
#             cog_store[residue] = universe.select_atoms("resid " + str(resid[residue])).center_of_geometry()
#
#         # Calculate a distance matrix
#
#         d = distance_array(np.array(cog_store).astype(np.float32), np.array(cog_store).astype(np.float32),
#                            box=u.dimensions, result=np.empty(shape=(N, N), dtype=np.float64), backend='OpenMP')
#
#     elif options.plot_type == "atom":
#
#         N = len(universe.select_atoms("protein").atoms) # pre-allocate to speed up calc
#
#         d = distance_array(np.array(universe.select_atoms("protein").positions).astype(np.float32),
#                            np.array(universe.select_atoms("protein").positions).astype(np.float32),
#                            box=u.dimensions, result=np.empty(shape=(N, N), dtype=np.float64), backend='OpenMP')
#
#     #Define a new heat map based on a user defined cut-off and convert to 1's & 0's
#
#     #heat_map_pop += (d < cut_off).astype(int)
#
#     heatmap += (d < cut_off).astype(int)
#
#     # return heat_map_pop
#     return heatmap
#
# def plot_hmap(data, residues,atoms, cut_off):
#
#     """plot a single frame
#     data = the populated hmap
#     names = list of amino acid names
#     resids = list of resids of amino acids
#     """
#     print "Making plot..."
#
#     data = (data / np.amax(data)) * 100  # normalise to make a percentage
#
#     # mask = np.tri(data.shape[0], k=-1)
#     # A = np.ma.array(data, mask=mask)  # mask out the lower triangle
#
#     fig = plt.figure()
#
#     ax = fig.add_subplot(111)
#
#     #colors = cm.ScalarMappable(cmap="viridis").to_rgba(data_value)
#
#     #surf = ax.plot_surface(x,y,z,rstride=1, cstride=1,linewidth=0, antialiased=True)
#
#     plt.title('Interaction Map of Contacts < ' + str(cut_off) + ' $\AA$', y=1.08)
#
#     cmap = CM.get_cmap('viridis', 10)  # jet doesn't have white color
#
#     cmap.set_bad('w')  # default value is 'k'
#
#     plt.imshow(data, cmap='viridis', interpolation='bicubic')
#     ax.grid(False)
#
#     if options.plot_type == "residue":
#
#         # Add lines to see where protein repeats start and stop
#         ax.axvline((len(residues)/num_protein), c='white', linestyle='--', lw=0.4)
#         ax.axvline((len(residues)/num_protein)*(num_protein - 1), c='white', linestyle='--', lw=0.4)
#         ax.axhline((len(residues) / num_protein), c='white', linestyle='--', lw=0.4)
#         ax.axhline((len(residues) / num_protein) * (num_protein - 1), c='white', linestyle='--', lw=0.4)
#
#         plt.xlabel("Residue Number")
#         plt.ylabel("Residue Number")
#
#         ## Annotate the chains...
#
#         ax.xaxis.set_tick_params(labeltop='on')
#
#         cent1 = ((len(residues) / num_protein) / 2)
#         cent2 = cent1 + (2 * cent1)
#         cent3 = cent1 + (4 * cent1)
#
#         # ann = ax.annotate('A', xy=(83, 83), xytext=(83, 83), xycoords='data',
#         #             fontsize=12, ha='center', va='bottom',
#         #             bbox=dict(boxstyle='square', fc='white'))
#         #
#         # ann2 = ax.annotate('B', xy=(249, 249), xytext=(249, 249), xycoords='data',
#         #                   fontsize=12, ha='center', va='bottom',
#         #                   bbox=dict(boxstyle='square', fc='white'))
#         #
#         # ann3 = ax.annotate('C', xy=(415, 415), xytext=(415, 415), xycoords='data',
#         #                   fontsize=12, ha='center', va='bottom',
#         #                   bbox=dict(boxstyle='square', fc='white'))
#
#         ann = ax.annotate('A', xy=(cent1, cent1), xytext=(cent1, cent1), xycoords='data',
#                     fontsize=12, ha='center', va='bottom',
#                     bbox=dict(boxstyle='square', fc='white'))
#
#         ann2 = ax.annotate('B', xy=(cent2, cent2), xytext=(cent2, cent2), xycoords='data',
#                           fontsize=12, ha='center', va='bottom',
#                           bbox=dict(boxstyle='square', fc='white'))
#
#         ann3 = ax.annotate('C', xy=(cent3, cent3), xytext=(cent3, cent3), xycoords='data',
#                           fontsize=12, ha='center', va='bottom',
#                           bbox=dict(boxstyle='square', fc='white'))
#
#     elif options.plot_type == "atom":
#
#         # Add lines to see where protein repeats start and stop
#         ax.axvline((len(atoms) / num_protein), c='white', linestyle='--', lw=0.4)
#         ax.axvline((len(atoms) / num_protein) * (num_protein - 1), c='white', linestyle='--', lw=0.4)
#         ax.axhline((len(atoms) / num_protein), c='white', linestyle='--', lw=0.4)
#         ax.axhline((len(atoms) / num_protein) * (num_protein - 1), c='white', linestyle='--', lw=0.4)
#
#         plt.xlabel("Atom Index")
#         plt.ylabel("Atom Index")
#
#         cent1 = ((len(atoms) / num_protein) / 2)
#         cent2 = cent1 + (2*cent1)
#         cent3 = cent1 + (4*cent1)
#
#         ## Annotate the chains...
#
#         ax.xaxis.set_tick_params(labeltop='on')
#
#         ann = ax.annotate('A', xy=(cent1, cent1), xytext=(cent1, cent1), xycoords='data',
#                           fontsize=12, ha='center', va='bottom',
#                           bbox=dict(boxstyle='square', fc='white'))
#
#         ann2 = ax.annotate('B', xy=(cent2, cent2), xytext=(cent2, cent2), xycoords='data',
#                            fontsize=12, ha='center', va='bottom',
#                            bbox=dict(boxstyle='square', fc='white'))
#
#         ann3 = ax.annotate('C', xy=(cent3, cent3), xytext=(cent3, cent3), xycoords='data',
#                            fontsize=12, ha='center', va='bottom',
#                            bbox=dict(boxstyle='square', fc='white'))
#
#     cbar = plt.colorbar()
#     cbar.ax.set_ylabel('Average of Interaction (%)', rotation=270)
#     cbar.ax.get_yaxis().labelpad = 20
#
#     return fig
#
# def plot_sub_plots(data, residues, atoms, cut_off, residue_names):
#
#     # This function currently only works for num proteins = 3, would be good to generalise this to any number soon.
#
#     N = int(len(residues))
#
#     print "Making subplots..."
#
#     '''plot a single frame
#     data = the populated hmap
#     names = list of amino acid names
#     resids = list of resids of amino acids
#     '''
#
#     data = (data / np.amax(data)) * 100  # normalise to make a percentage
#
#     # Get interaction columns
#     ints_on_a = data[0:(N / num_protein), 0:(3 * (N / num_protein))]
#     ints_on_b = data[N / num_protein:(2 * (N / num_protein)), 0:(3 * (N / num_protein))]
#     ints_on_c = data[2 * (N / num_protein):(3 * (N / num_protein)), 0:(3 * (N / num_protein))]
#
#
#     print(ints_on_a)
#     print(ints_on_b)
#     print(ints_on_c)
#
#
#     # sum_ints_on_a = np.sum(ints_on_a, axis=1) / 100
#     # sum_ints_on_b = np.sum(ints_on_b, axis=1) / 100
#     # sum_ints_on_c = np.sum(ints_on_c, axis=1) / 100
#
#     # Sum (down columns) all of the interactions on each protein. You need to minus the contribution made from the
#     # protein contacts made with itself so you are then left with the interactions made with other proteins in the
#     # system.
#
#     sum_ints_on_a = (np.sum(ints_on_a, axis=1) - np.sum(data[0:(N / num_protein), 0:(N / num_protein)],
#                                                         axis=1))
#     sum_ints_on_b = (np.sum(ints_on_b, axis=1) - np.sum(data[N  /num_protein:(2 * (N / num_protein)), N / num_protein:(2 * (N / num_protein))],
#                                                        axis=1))
#     sum_ints_on_c = (np.sum(ints_on_c, axis=1) - np.sum(data[2 * (N / num_protein):(3 * (N / num_protein)), 2 * (N / num_protein):(3 * (N / num_protein))],
#                                                         axis=1))
#
#     #Normalise interactions on each chain
#     sum_ints_on_a = (sum_ints_on_a / np.amax(sum_ints_on_a)) * 100
#     sum_ints_on_b = (sum_ints_on_b / np.amax(sum_ints_on_b)) * 100
#     sum_ints_on_c = (sum_ints_on_c / np.amax(sum_ints_on_c)) * 100
#
#
#     fig = plt.figure()
#
#     ax = fig.add_subplot(111)
#
#     # make xlabels (the resids) and +1 due to 0 index.
#
#     x = [i + 1 for i in range(len(sum_ints_on_a))]
#
#     ax.bar(x, sum_ints_on_a, label='Chain A')
#     ax.bar(x, sum_ints_on_b, label='Chain B')
#     ax.bar(x, sum_ints_on_c, label='Chain C')
#
#     ax.set_xlabel('Intermolecular Interaction (%)')
#     ax.set_ylabel('Residue Number')
#
#     plt.legend()
#
#     plt.savefig('bar.svg', format='svg', dpi=300)
#
#     plt.show()
#
#
#     # fig = plt.figure()
#     #
#     # #ax = fig.add_subplot(111)
#     #
#     # ax = sns.barplot(sum_ints_on_a)#, hue='A')#, shade=True)
#     # ax = sns.barplot(sum_ints_on_b)#, hue='B')#, shade=True)
#     # ax = sns.barplot(sum_ints_on_c)#, hue='C')#, shade=True)
#     #
#     #
#     # plt.show()
#
#
#     # # print(sum_ints_on_a[:, 0])
#     # #
#     # df = pd.DataFrame.from_dict(
#     #     {
#     #         'Chain': [1],#, 2, 3],
#     #         'Resid': range(len(sum_ints_on_a)),
#     #         'Count': [sum_ints_on_a.flatten()]#, sum_ints_on_b.flatten(), sum_ints_on_c.flatten()]
#     #     }
#     # )
#     #
#     # print(df)
#     # print(df['Count'][0].flatten().shape)
#     #
#     # da = {'chain': ['A' for i in range(len(sum_ints_on_a))], 'ints': sum_ints_on_a}
#     # db = {'chain': ['B' for i in range(len(sum_ints_on_b))], 'ints': sum_ints_on_b}
#     # dc = {'chain': ['C' for i in range(len(sum_ints_on_c))], 'ints': sum_ints_on_c}
#     #
#     #
#     #
#     #
#     # print(da)
#     #
#     # #df = pd.melt(df, id_vars='')
#     #
#     # plt.clf()
#     #
#     # sns.barplot(x)
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#     data_1_2 = data[0:(N / num_protein), (N / num_protein):(2 * (N / num_protein))]           # Protein A interacting with Protein B
#     data_1_3 = data[0:(N / num_protein), (2*(N / num_protein)):(3 * (N / num_protein))]       # Protein A interacting with Protein C
#     data_2_3 = data[(N / num_protein):(2 * (N / num_protein)), (2*(N / num_protein)):(3 * (N / num_protein))]       # Protein B interacting with Protein C
#
#
#     sub_plot_data_list = [data_1_2, data_1_3, data_2_3]
#
#     for i in range(len(sub_plot_data_list)):
#
#         if i == 0:
#
#             xlab = "Protein B"
#             ylab = "Protein A"
#             focus = "AB"
#
#         elif i == 1:
#
#             xlab = "Protein C"
#             ylab = "Protein A"
#             focus = "AC"
#
#         elif i == 2:
#
#             xlab = "Protein C"
#             ylab = "Protein B"
#             focus = "BC"
#
#         sub_fig = plt.figure()
#
#         ax = sub_fig.add_subplot(111)
#
#         if options.plot_type == "residue":
#
#             plt.xlabel("Residue Number (" + str(xlab) + ")")
#             plt.ylabel("Residue Number (" + str(ylab) + ")")
#
#             ax.grid(linestyle='--', linewidth=1)
#             ax.xaxis.set_tick_params(labeltop='on')
#
#             plt.title('Interaction Map of Contacts < ' + str(cut_off) + ' $\AA$', y=1.08)
#
#             plt.imshow(sub_plot_data_list[i], cmap='viridis', interpolation='bicubic')
#
#             cbar = plt.colorbar()
#             cbar.ax.set_ylabel('Average of Interaction (%)', rotation=270)
#             cbar.ax.get_yaxis().labelpad = 20
#
#             sub_fig.savefig('sub_figure_' + str(options.plot_type) + str(i) + '.svg', format='svg')
#
#             sub_fig.clf()
#
#
#         #### bar chart plot ####
#
#
#             bar_data_0 = np.sum(sub_plot_data_list[i], axis=0) / 100 # Calculate sum of interactions for protein on x axis of heat map
#             bar_data_1 = np.sum(sub_plot_data_list[i], axis=1) / 100 # Calculate sum of interactions for protein on y axis of heat map
#
#             bar_data_0_30 = bar_data_0[(bar_data_0 >= 30)] # filter out values only higher than 30 %
#             bar_data_1_30 = bar_data_1[(bar_data_1 >= 30)]  # filter out values only higher than 30 %
#
#             resid_x0_labs = (np.where(bar_data_0 >= 30))  # Get the resid's of the residues in contact >= 30% of the time
#             resid_x1_labs = (np.where(bar_data_1 >= 30))  # Get the resid's of the residues in contact >= 30% of the time
#
#             resid_x0_labs = list(resid_x0_labs[0])  # Need to convert to a list for later
#             resid_x1_labs = list(resid_x1_labs[0])
#
#             #print resid_x1_labs
#
#             #print residue_names[0:(N/3)]
#
#             ### sorting out axis labels ###
#
#             resname_x0_labs = [residue_names[0:(N / 3)][k - 1] for k in resid_x0_labs] # extract the correct names
#
#             resname_x1_labs = [residue_names[0:(N/3)][k - 1] for k in resid_x1_labs]
#
#             resname_resnum_x0_labs = ([m + str(n) for m, n in zip(list(resname_x0_labs), resid_x0_labs)]) # combine the names and the resid number
#
#             resname_resnum_x1_labs = ([m + str(n) for m, n in zip(list(resname_x1_labs), resid_x1_labs)])
#
#             #print resname_resnum_x1_labs
#
#             ### Begin plotting ####
#
#             for j in range(2): # need to know if summed over rows or down columns of each sub heatmap plot...
#
#                 print ("j = " + str(j))
#
#                 sub_bar_fig = plt.figure()
#
#                 ax = sub_bar_fig.add_subplot(111)
#
#                 if j == 0: # we are looking at the sum down columns
#
#                     # plt.xticks(range(len(resid_x0_labs[0])), list(resid_x0_labs[0]))
#
#                     plt.xticks(range(len(resname_resnum_x0_labs)), list(resname_resnum_x0_labs), rotation='vertical')
#
#                     plt.title(str(ylab) + ' vs. ' + str(xlab) + ': Interaction of Contacts < ' + str(cut_off) + ' $\AA$ (.ge. 30%)', y=1.08)
#
#                     plt.xlabel("Residue Number " + str(xlab))
#                     plt.ylabel("Interaction (%)")
#
#                     plt.bar(range(len(bar_data_0_30)), bar_data_0_30)
#
#                 elif j == 1: # we are looking at the sum across rows
#
#                     # plt.xticks(range(len(resid_x1_labs[0])), list(resid_x1_labs[0]))
#
#                     plt.xticks(range(len(resname_resnum_x1_labs)), list(resname_resnum_x1_labs), rotation='vertical')
#
#                     plt.title(str(ylab) + ' vs. ' + str(xlab) + ': Interaction of Contacts < ' + str(cut_off) + ' $\AA$ (.ge. 30%)', y=1.08)
#
#                     plt.xlabel("Residue Number of " + str(ylab))
#                     plt.ylabel("Interaction (%)")
#
#                     plt.bar(range(len(bar_data_1_30)), bar_data_1_30)
#
#                 sub_bar_fig.savefig('sub_bar_figure_' + str(options.plot_type) + str(focus) + str(j) + '.svg', format='svg')
#
# def assign_beta_values(universe, residue_ids): #### STILL IN TEST PHASE ####
#
#     """
#
#     Takes the universe supplied and colours the resides based on their contact map vlaue. Two options can be used.
#
#     1) "residue": this colours each residue according to if their COM is within the defined cut off (faster)
#     2) "atom": this colours each atom according to if their COM is within the defined cut off (slower)
#
#     """
#
#     print "Writing contacts to PDB file..."
#
#     u.trajectory[-1]  # reset the trajectory to the final frame prior to writing the beta values
#
#     protein_atom_selection = u.select_atoms("protein")
#
#     #protein_residue_selection = u.select_atoms("resid 1:" + str(len(residue_ids)))  # TO FIX!!!!!
#
#     #protein_residue_selection = u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490) and not backbone")
#
#     protein_residue_selection = u.select_atoms("protein")
#
#     if options.plot_type == "residue":
#
#         residues_per_protein = (len(residue_ids) / num_protein)
#
#         prot_1_2_array = heat_map_pop[0:(residues_per_protein), (residues_per_protein):((residues_per_protein) * 2)]
#
#         prot_1_3_array = heat_map_pop[0:(residues_per_protein), (residues_per_protein * 2):(residues_per_protein * 3)]
#
#         prot_2_3_array = heat_map_pop[(residues_per_protein):((residues_per_protein) * 2),
#                                (residues_per_protein * 2):(residues_per_protein * 3)]
#
#         # temporary fix (from MDAnalysis site: https://www.mdanalysis.org/MDAnalysisTutorial/writing.html)
#         u.add_TopologyAttr(mda.core.topologyattrs.Tempfactors(np.zeros(len(u.atoms))))
#
#         cat_arrays = np.concatenate([prot_1_2_array.mean(0), prot_2_3_array.mean(0), prot_1_3_array.mean(0)])
#
#     elif options.plot_type == "atom":
#
#         atoms_per_protein = (len(universe.select_atoms("protein").positions) / num_protein)
#
#         prot_1_2_array = heat_map_pop[0:(atoms_per_protein), (atoms_per_protein):((atoms_per_protein) * 2)]
#
#         prot_1_3_array = heat_map_pop[0:(atoms_per_protein), (atoms_per_protein * 2):(atoms_per_protein * 3)]
#
#         prot_2_3_array = heat_map_pop[(atoms_per_protein):((atoms_per_protein) * 2),
#                         (atoms_per_protein * 2):(atoms_per_protein * 3)]
#
#         # temporary fix (from MDAnalysis site: https://www.mdanalysis.org/MDAnalysisTutorial/writing.html)
#         u.add_TopologyAttr(mda.core.topologyattrs.Tempfactors(np.zeros(len(u.atoms))))
#
#         cat_arrays = np.concatenate([prot_1_2_array.mean(0), prot_2_3_array.mean(0), prot_1_3_array.mean(0)])
#
#     if options.plot_type == "residue":
#
#         #beta_residue_array = np.zeros((len(np.asarray(u.select_atoms("protein").positions)), 1))
#
#         beta_residue_array = np.zeros((len(np.asarray(u.select_atoms("protein").positions))))
#
#         #beta_residue_array = np.zeros((len(np.asarray(u.select_atoms("(resid 138:158 or resid 304:324 or resid 470:490)").positions)), 1))
#
#         print residue_ids
#
#         for i in range(len(residue_ids)):
#
#             ##### SPECIFIC #####
#
#             if options.region == "specific":
#
#                 residue_coords = u.select_atoms("resid " + str(residue_ids[i])).positions
#
#                 residue_coords_corrected = []
#
#                 for j in range(len(residue_coords)):
#
#                     residue_coords_corrected.append(range(np.size(residue_coords))[j] + u.select_atoms("resid " + str(residue_ids[i])).atoms.indices[0])
#
#                 beta_residue_array[residue_coords_corrected] = cat_arrays[i]
#
#             #### GENERAL #####
#
#             if options.region == "all":
#
#                 residue_coords = u.select_atoms("resid " + str(i + 1)).positions  # select every atom of a residue
#
#                 if i == 0:
#
#                     beta_residue_array[[range(np.size(residue_coords))]] = cat_arrays[i]
#
#                     prev_indices = range(np.size(residue_coords, 0))
#
#                     index_max = np.max(prev_indices) # store the max index number in the first instance. +1 due to 0-indexing
#
#                 elif i > 0:
#
#                     current_indices = range(np.size(residue_coords, 0))
#
#                     new_current_indices = [x + (index_max + 1) for x in current_indices] # updating the number...
#
#                     beta_residue_array[[new_current_indices]] = cat_arrays[i]
#
#                     # for next loop...
#
#                     #current_indices = new_current_indices
#
#                     index_max += (np.max(range(np.size(residue_coords, 0))) + 1)
#
#         protein_residue_selection.tempfactors = beta_residue_array
#
#         protein_residue_selection.write("residue_bfact.pdb", format("PDB"))
#
#     elif options.plot_type == "atom":
#
#         protein_atom_selection.tempfactors = cat_arrays
#
#         protein_atom_selection.write("atom_bfact.pdb", format("PDB"))
#
#         protein_atom_selection.write()
#
#     # BELOW is commented out since it worked only with older verison of mda (pre 0.17.0)
#
#     # for i, b in enumerate(np.concatenate([prot_atoms_1_2_array.mean(0), prot_atoms_2_3_array.mean(0), prot_atoms_1_3_array.mean(0)])):
#     #
#     #     protein_selection.select_atoms("bynum " + str(i)).tempfactors = b
#
#
# if __name__ == "__main__":
#
#     parser = argparse.ArgumentParser(
#         description="Calculates the contacts between chains")
#     parser.add_argument("-c", dest="gro_file", type=str, help='the coordinate file [.gro]')
#     parser.add_argument("-f", dest="xtc_file", type=str,
#                         help='a corrected trajectory file, pbc artifacts removed and the protein centered')
#     parser.add_argument("-d", dest="cut_off_value", type=float, help='the cut-off value')
#     parser.add_argument("-p", dest="plot_type", type=str,
#                         help="define the heatplot type, i.e residue - residue or atom - atom.")
#     parser.add_argument("-region", dest="region", type=str,
#                         help="decide to analyse all of the protein or a specific region: 'all' or 'specific'",
#                         required=True, default="all")
#     parser.add_argument("-sel", dest="selection", type=str,
#                         help="if -region flag included, this is the selection string. e.g. resid 1:100")
#     parser.add_argument("-skip", dest="skip", type=int, default=0,
#                         help="No. of frames to skip, default = 0")
#
#     options = parser.parse_args()
#
#     if options.region == 'specific' and options.selection == None:
#         parser.error("-region 'specific' requires -sel flag, make sure you have included the selection!")
#
#     startTime = datetime.now()
#
#     residue_ids, atom_ids, initial_residue_heat_map, initial_atom_heat_map, u, resnames = make_hmap(coord=options.gro_file, traj=options.xtc_file)
#
#
#     for frame in u.trajectory[::options.skip]:
#
#         if u.trajectory.frame % 10 == 0:
#             print "Frame = " + str(u.trajectory.frame)
#
#         # if u.trajectory.frame == 2:
#         #     break
#
#         u.trajectory[frame.frame]
#
#         if options.plot_type == "residue":
#
#             heat_map_pop = populate_hmap(heatmap=initial_residue_heat_map, universe=u, resid=residue_ids, cut_off=options.cut_off_value)
#
#         elif options.plot_type == "atom":
#
#             heat_map_pop = populate_hmap(heatmap=initial_atom_heat_map, universe=u, resid=residue_ids, cut_off=options.cut_off_value)
#
#     #try:
#     assign_beta_values(universe=u, residue_ids=residue_ids)
#     #except Exception:
#         #pass
#
#     identify_residues = heat_map_pop.astype(str)
#
#     # Plot the whole hmap
#     fig = plot_hmap(data=heat_map_pop, residues=residue_ids, atoms=atom_ids, cut_off=options.cut_off_value)
#
#     # Plot each heatmap for each protein - proein interaction
#     plot_sub_plots(data=heat_map_pop, residues=residue_ids, atoms=atom_ids, cut_off=options.cut_off_value, residue_names=resnames)
#
#     fig.savefig('figure_' + str(options.plot_type) + '.svg', format='svg')
#     fig.clf()
#
#     print "Time taken = " + str(datetime.now() - startTime)
