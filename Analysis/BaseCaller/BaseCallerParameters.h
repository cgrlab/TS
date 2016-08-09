/* Copyright (C) 2014 Ion Torrent Systems, Inc. All Rights Reserved */

//! @file     BaseCallerParameters.h
//! @ingroup  BaseCaller
//! @brief    Command line option reading and storage for BaseCaller modules

#ifndef BASECALLERPARAMETERS_H
#define BASECALLERPARAMETERS_H

#include <stdio.h>
#include <time.h>
#include <math.h>
#include <assert.h>
#include <algorithm>
#include <string>
#include <pthread.h>
#include <stdint.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <deque>
#include <iostream>
#include <set>
#include <vector>

#include "json/json.h"
#include "LinuxCompat.h"
#include "IonErr.h"
#include "OptArgs.h"
#include "IonVersion.h"
#include "file-io/ion_util.h"
#include "Utils.h"
#include "RawWells.h"

#include "BaseCallerUtils.h"
#include "DPTreephaser.h"
#include "BarcodeDatasets.h"
#include "BarcodeClassifier.h"
#include "OrderedDatasetWriter.h"
#include "TreephaserSSE.h"
#include "PhaseEstimator.h"
#include "PerBaseQual.h"
#include "BaseCallerFilters.h"
#include "BaseCallerMetricSaver.h"
//#include "LinearCalibrationModel.h"

using namespace std;

// Forward declaration of classes
class HistogramCalibration;
class LinearCalibrationModel;

//! @brief    Verify path exists and if it does, canonicalize it
//! @ingroup  BaseCaller
void ValidateAndCanonicalizePath(string &path);

//! @brief    Verify path exists and if it does, canonicalize it. If it doesn't, try fallback location
//! @ingroup  BaseCaller
void ValidateAndCanonicalizePath(string &path, const string& backup_path);


// =======================================================================
// Different structs grouping input parameters by use and module

struct BaseCallerFiles
{
    string    input_directory;
    string    output_directory;
    string    unfiltered_untrimmed_directory;
    string    unfiltered_trimmed_directory;

    string    filename_wells;
    string    filename_mask;
    string    filename_filter_mask;
    string    filename_json;

    string    lib_datasets_file;      //!< Datasets file containing all the barcodes that are used in the run
    string    calibration_panel_file; //!< Datasets file containing the barcodes that are used for calibration panel

    bool      options_set;
};

// ------------------------------------------------------------

struct BCwellSampling
{
    int       num_unfiltered;        //!< Reservoir sampled number of wells to be written out unfiltered.
    int       downsample_size;       //!< Reservoir sampled number of the wells on the chip.
    float     downsample_fraction;   //!< Reservoir sampled fraction of the wells on the chip.

    int       calibration_training;  //!< Number of wells to be sampled for calibration training
    bool      have_calib_panel;      //!< Inidactes the presence of a calibration panel in this run
    MaskType  MaskNotWanted;         //!< Type of beads to be excluded from sampling (e.g. for cal. training)

    bool      options_set;
};

// ------------------------------------------------------------
// Context variables that the worker threads need to be aware of.

struct BCcontextVars {

    string    run_id;                 //!< Run ID string, prepended to each read name
    int       extra_trim_left;        //!< Number of additional insert bases past key and barcode to be trimmed
    bool      process_tfs;            //!< If set to false, TF-related BAM will not be generated
    bool      only_process_unfiltered_set;
    string    flow_signals_type;      //!< The flow signal type: "default" - Normalized and phased,
                                      //                         "wells" - Raw values (unnormalized and not dephased),
                                      //                         "key-normalized" - Key normalized and not dephased,
                                      //                         "adaptive-normalized" - Adaptive normalized and not dephased, and
                                      //                         "unclipped" - Normalized and phased but unclipped.

    // Treephaser options
    string    keynormalizer;          //!< Name of selected key normalization algorithm
    string    dephaser;               //!< Name of selected dephasing algorithm
    int       windowSize;             //!< Normalization window size
    bool      diagonal_state_prog;    //!< Switch to enable a diagonal state progression
    bool      skip_droop;             //!< Switch to include / exclude droop in cpp basecaller
    bool      skip_recal_during_norm; //!< Switch to exclude recalibration from the normalization stage

    bool options_set;
};

// ==============================================================================
//! @brief    Information needed by BaseCaller worker threads
//! @ingroup  BaseCaller

struct BaseCallerContext {

    // General run parameters
    string                    run_id;                 //!< Run ID string, prepended to each read name
    string                    keynormalizer;          //!< Name of selected key normalization algorithm
    string                    dephaser;               //!< Name of selected dephasing algorithm
    string                    filename_wells;         //!< Filename of the input wells file
    ion::FlowOrder            flow_order;             //!< Flow order object, also stores number of flows
    vector<KeySequence>       keys;                   //!< Info about key sequences in use by library and TFs
    string                    flow_signals_type;      //!< The flow signal type: "default" - Normalized and phased, "wells" - Raw values (unnormalized and not dephased), "key-normalized" - Key normalized and not dephased, "adaptive-normalized" - Adaptive normalized and not dephased, and "unclipped" - Normalized and phased but unclipped.
    string                    output_directory;       //!< Root directory for all output files
    int                       extra_trim_left;        //!< Number of additional insert bases past key and barcode to be trimmed
    bool                      process_tfs;            //!< If set to false, TF-related BAM will not be generated
    int                       windowSize;             //!< Normalization window size
    bool                      have_calibration_panel; //!< Signales the presence of a recalibration panel
    bool                      calibration_training;   //!< Is BaseCaller in calibration training mode?
    bool                      diagonal_state_prog;    //!< Switch to enable a diagonal state progression
    bool                      only_process_unfiltered_set;
    bool                      skip_droop;             //!< Switch to include / exclude droop in cpp basecaller
    bool                      skip_recal_during_norm; //!< Switch to exclude recalibration from the normalization stage

    // Important outside entities accessed by BaseCaller
    ion::ChipSubset           chip_subset;            //!< Chip coordinate & region handling for Basecaller
    Mask                      *mask;                  //!< Beadfind and filtering outcomes for wells
    BaseCallerFilters         *filters;               //!< Filter configuration and stats
    PhaseEstimator            estimator;              //!< Phasing estimation results
    PerBaseQual               quality_generator;      //!< Base phred quality value generator
    vector<int>               class_map;              //!< What to do with each well
    BaseCallerMetricSaver     *metric_saver;          //!< Saves requested metrics to an hdf5
    BarcodeClassifier         *barcodes;              //!< Barcode detection and trimming
    BarcodeClassifier         *calibration_barcodes;  //!< Barcode detection for calibration set
    HistogramCalibration      *histogram_calibration; //!< Posterior base call and signal adjustment algorithm
    LinearCalibrationModel    *linear_cal_model;      //!< Model estimation of simulated predictions and observed measurements
    PolyclonalFilterOpts      polyclonal_filter;      //!< User options for polyclonal filtering

    // Threaded processing
    pthread_mutex_t           mutex;                  //!< Shared read/write mutex for BaseCaller worker threads

    // Basecalling results saved here
    OrderedDatasetWriter      lib_writer;                 //!< Writer object for library BAMs
    OrderedDatasetWriter      calib_writer;               //!< Writer object for calibration barcode BAMs
    OrderedDatasetWriter      tf_writer;                  //!< Writer object for test fragment BAMs
    set<unsigned int>         unfiltered_set;             //!< Indicates which wells are to be saved to unfiltered BAMs
    OrderedDatasetWriter      unfiltered_writer;          //!< Writer object for unfiltered BAMs for a random subset of library reads
    OrderedDatasetWriter      unfiltered_trimmed_writer;  //!< Writer object for unfiltered trimmed BAMs for a random subset of library reads

    bool SetKeyAndFlowOrder(OptArgs& opts, const char * FlowOrder, const int NumFlows);

    bool WriteUnfilteredFilterStatus(const BaseCallerFiles & bc_files);
};


// =======================================================================

class BaseCallerParameters {
public:
    BaseCallerParameters() {
      num_threads_              = 1;
      num_bamwriter_threads_    = 1;
      bc_files.options_set      = false;
      sampling_opts.options_set = false;
      context_vars.options_set  = false;
    };

    void PrintHelp();

    bool InitializeFilesFromOptArgs(OptArgs& opts);

    bool InitContextVarsFromOptArgs(OptArgs& opts);

    bool InitializeSamplingFromOptArgs(OptArgs& opts, const int num_wells); // Needs chip subset size to reconcile options

    bool SetBaseCallerContextVars(BaseCallerContext & bc);

    bool SaveParamsToJson(Json::Value& basecaller_json, const BaseCallerContext& bc, const string& chip_type);


    const BaseCallerFiles & GetFiles() const {
     if (not bc_files.options_set){
       cerr << "BaseCallerParameters::GetFiles: Options need to be initialized before they can be used." << endl;
       exit(EXIT_FAILURE);
     }
     return bc_files;
    };


    const BCwellSampling & GetSamplingOpts() const {
      if (not sampling_opts.options_set){
        cerr << "BaseCallerParameters::GetSamplingOpts: Options need to be initialized before they can be used." << endl;
        exit(EXIT_FAILURE);
      }
      return sampling_opts;
    };

    int NumThreads()          const { return num_threads_; };
    int NumBamWriterThreads() const { return num_bamwriter_threads_; };

private:
    int                 num_threads_;              //!< NUmber of worker threads to do base calling
    int                 num_bamwriter_threads_;    //!< Number of threads one bam writer object uses
    BaseCallerFiles     bc_files;
    BCcontextVars       context_vars;
    BCwellSampling      sampling_opts;
};


#endif // BASECALLERPARAMETERS_H