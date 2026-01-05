// ============================================================================
// APB Interface
// ============================================================================
// Interface SystemVerilog pour connecter le testbench UVM au DUT
// ============================================================================

interface apb_if #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32
) (
    input logic pclk,
    input logic preset_n
);

    // =========================================================================
    // Signaux APB
    // =========================================================================

    // Master -> Slave
    logic                    psel;
    logic                    penable;
    logic                    pwrite;
    logic [ADDR_WIDTH-1:0]   paddr;
    logic [DATA_WIDTH-1:0]   pwdata;

    // Slave -> Master
    logic                    pready;
    logic [DATA_WIDTH-1:0]   prdata;
    logic                    pslverr;

    // =========================================================================
    // Clocking Blocks
    // =========================================================================
    // Les clocking blocks définissent QUAND échantillonner les signaux
    // - Le driver utilise le clocking block "driver_cb"
    // - Le monitor utilise le clocking block "monitor_cb"

    // TODO 1: Complète le clocking block du driver
    // Le driver ENVOIE (output) les signaux master et LIT (input) les signaux slave
    clocking driver_cb @(posedge pclk);
        default input #1step output #1step;
        output psel;
        output penable;
        output pwrite;
        output paddr;
        output pwdata;
        input  pready;
        input  prdata;
        input  pslverr;
    endclocking

    // TODO 2: Complète le clocking block du monitor
    // Le monitor ne fait que LIRE (input) tous les signaux
    clocking monitor_cb @(posedge pclk);
        default input #1step;
        input psel;
        input penable;
        input pwrite;
        input paddr;
        input pwdata;
        input pready;
        input prdata;
        input pslverr;
    endclocking

    // =========================================================================
    // Modports
    // =========================================================================
    // Les modports définissent les "vues" de l'interface

    modport driver  (clocking driver_cb,  input pclk, input preset_n);
    modport monitor (clocking monitor_cb, input pclk, input preset_n);

endinterface
