// ============================================================================
// APB Package
// ============================================================================
// Regroupe toutes les classes UVM du testbench
// ============================================================================

package apb_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // Classes UVM (ordre important: dépendances d'abord)
    `include "apb_seq_item.sv"
    `include "apb_driver.sv"
    `include "apb_monitor.sv"
    `include "apb_agent.sv"
    `include "apb_scoreboard.sv"
    `include "apb_env.sv"
    `include "apb_sequences.sv"
    `include "apb_test.sv"

endpackage
