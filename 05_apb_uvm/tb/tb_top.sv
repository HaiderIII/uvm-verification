// ============================================================================
// APB Testbench Top
// ============================================================================
// Module top-level qui instancie le DUT et connecte l'interface
// ============================================================================

`timescale 1ns/1ps

module tb_top;

    import uvm_pkg::*;
    import apb_pkg::*;

    // =========================================================================
    // Signaux d'horloge et reset
    // =========================================================================
    logic pclk;
    logic preset_n;

    // =========================================================================
    // Génération de l'horloge (100 MHz = 10ns période)
    // =========================================================================
    initial begin
        pclk = 0;
        forever #5 pclk = ~pclk;
    end

    // =========================================================================
    // Génération du reset
    // =========================================================================
    initial begin
        preset_n = 0;
        #50;
        preset_n = 1;
    end

    // =========================================================================
    // Interface APB
    // =========================================================================
    apb_if apb_vif(pclk, preset_n);

    // =========================================================================
    // DUT - APB Slave
    // =========================================================================
    apb_slave #(
        .ADDR_WIDTH(8),
        .DATA_WIDTH(32)
    ) dut (
        .pclk     (pclk),
        .preset_n (preset_n),
        .psel     (apb_vif.psel),
        .penable  (apb_vif.penable),
        .pwrite   (apb_vif.pwrite),
        .paddr    (apb_vif.paddr),
        .pwdata   (apb_vif.pwdata),
        .pready   (apb_vif.pready),
        .prdata   (apb_vif.prdata),
        .pslverr  (apb_vif.pslverr)
    );

    // =========================================================================
    // Configuration UVM et lancement
    // =========================================================================
    initial begin
        // Passer l'interface au testbench via config_db
        uvm_config_db#(virtual apb_if)::set(null, "*", "vif", apb_vif);

        // Lancer le test UVM
        run_test("apb_base_test");
    end

    // =========================================================================
    // Dump des waveforms (optionnel)
    // =========================================================================
    initial begin
        $dumpfile("apb_test.vcd");
        $dumpvars(0, tb_top);
    end

endmodule
