// ============================================================================
// APB Slave - 4 registres de 32 bits
// ============================================================================
// Adresses:
//   0x00 - REG0 (R/W)
//   0x04 - REG1 (R/W)
//   0x08 - REG2 (R/W)
//   0x0C - REG3 (R/W)
// ============================================================================

module apb_slave #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32
) (
    input  logic                    pclk,
    input  logic                    preset_n,

    // APB Slave Interface
    input  logic                    psel,
    input  logic                    penable,
    input  logic                    pwrite,
    input  logic [ADDR_WIDTH-1:0]   paddr,
    input  logic [DATA_WIDTH-1:0]   pwdata,
    output logic                    pready,
    output logic [DATA_WIDTH-1:0]   prdata,
    output logic                    pslverr
);

    // =========================================================================
    // Registres internes
    // =========================================================================
    logic [DATA_WIDTH-1:0] reg_file [0:3];  // 4 registres

    // =========================================================================
    // TODO 1: Calcul de l'index du registre
    // =========================================================================
    // L'adresse est alignée sur 4 octets (0x00, 0x04, 0x08, 0x0C)
    // Pour obtenir l'index (0, 1, 2, 3), il faut diviser par 4
    // En binaire, diviser par 4 = décaler de 2 bits à droite = paddr[3:2]

    logic [1:0] reg_index;
    assign reg_index = paddr[3:2];

    // =========================================================================
    // TODO 2: Détection d'adresse valide
    // =========================================================================
    // Adresse valide si <= 0x0C (dernier registre)

    logic addr_valid;
    assign addr_valid = (paddr <= 4'h0C);

    // =========================================================================
    // TODO 3: Condition de transfert APB
    // =========================================================================
    // Un transfert est complété quand les 3 conditions sont réunies:
    // - psel = 1 (slave sélectionné)
    // - penable = 1 (phase ACCESS)
    // - pready = 1 (slave prêt)

    logic transfer_valid;
    assign transfer_valid = psel & penable & pready;

    // =========================================================================
    // PREADY - Toujours prêt (pas de wait states)
    // =========================================================================
    assign pready = 1'b1;

    // =========================================================================
    // TODO 4: PSLVERR - Erreur si adresse invalide PENDANT un transfert
    // =========================================================================
    assign pslverr = psel & penable & !addr_valid;

    // =========================================================================
    // TODO 5: Logique d'écriture
    // =========================================================================
    always_ff @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            // Reset tous les registres à 0
            reg_file[0] <= '0;
            reg_file[1] <= '0;
            reg_file[2] <= '0;
            reg_file[3] <= '0;
        end
        else if (pwrite & transfer_valid) begin
            // Écrire dans le registre sélectionné
            reg_file[reg_index] <= pwdata;
        end
    end

    // =========================================================================
    // TODO 6: Logique de lecture (combinatoire)
    // =========================================================================
    always_comb begin
        if (!pwrite & transfer_valid) begin
            prdata = reg_file[reg_index];
        end
        else begin
            prdata = '0;
        end
    end

endmodule
