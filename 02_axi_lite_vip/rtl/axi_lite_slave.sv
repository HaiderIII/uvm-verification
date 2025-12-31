// AXI-Lite Slave - Bloc de 4 registres 32-bit
//
// Adresses :
//   0x00 : Registre 0 (R/W)
//   0x04 : Registre 1 (R/W)
//   0x08 : Registre 2 (R/W)
//   0x0C : Registre 3 (R/W)

module axi_lite_slave #(
    parameter ADDR_WIDTH = 4,   // 4 bits = 16 adresses possibles
    parameter DATA_WIDTH = 32   // 32 bits de données
) (
    // Global signals
    input  logic                    clk,
    input  logic                    rst_n,

    // Write Address Channel (AW)
    input  logic [ADDR_WIDTH-1:0]   s_axi_awaddr,
    input  logic                    s_axi_awvalid,
    output logic                    s_axi_awready,

    // Write Data Channel (W)
    input  logic [DATA_WIDTH-1:0]   s_axi_wdata,
    input  logic [DATA_WIDTH/8-1:0] s_axi_wstrb,   // Byte strobes
    input  logic                    s_axi_wvalid,
    output logic                    s_axi_wready,

    // Write Response Channel (B)
    output logic [1:0]              s_axi_bresp,
    output logic                    s_axi_bvalid,
    input  logic                    s_axi_bready,

    // Read Address Channel (AR)
    input  logic [ADDR_WIDTH-1:0]   s_axi_araddr,
    input  logic                    s_axi_arvalid,
    output logic                    s_axi_arready,

    // Read Data Channel (R)
    output logic [DATA_WIDTH-1:0]   s_axi_rdata,
    output logic [1:0]              s_axi_rresp,
    output logic                    s_axi_rvalid,
    input  logic                    s_axi_rready
);

    // Response codes
    localparam RESP_OKAY   = 2'b00;
    localparam RESP_SLVERR = 2'b10;

    // Registres internes (4 x 32 bits)
    logic [DATA_WIDTH-1:0] registers [0:3];

    // États internes
    logic [ADDR_WIDTH-1:0] write_addr;
    logic [ADDR_WIDTH-1:0] read_addr;
    logic write_addr_received;
    logic write_data_received;

    // =========================================================================
    // Write Address Channel
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_awready <= 1'b1;  // Ready par défaut
            write_addr <= '0;
            write_addr_received <= 1'b0;
        end else begin
            if (s_axi_awvalid && s_axi_awready) begin
                // Handshake réussi : capturer l'adresse
                write_addr <= s_axi_awaddr;
                write_addr_received <= 1'b1;
                s_axi_awready <= 1'b0;  // Plus prêt jusqu'à fin de transaction
            end else if (s_axi_bvalid && s_axi_bready) begin
                // Transaction terminée : prêt pour la suivante
                s_axi_awready <= 1'b1;
                write_addr_received <= 1'b0;
            end
        end
    end

    // =========================================================================
    // Write Data Channel
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_wready <= 1'b1;  // Ready par défaut
            write_data_received <= 1'b0;
        end else begin
            if (s_axi_wvalid && s_axi_wready) begin
                // Handshake réussi
                write_data_received <= 1'b1;
                s_axi_wready <= 1'b0;
            end else if (s_axi_bvalid && s_axi_bready) begin
                // Transaction terminée
                s_axi_wready <= 1'b1;
                write_data_received <= 1'b0;
            end
        end
    end

    // =========================================================================
    // Écriture dans les registres
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            registers[0] <= 32'h0000_0000;
            registers[1] <= 32'h0000_0000;
            registers[2] <= 32'h0000_0000;
            registers[3] <= 32'h0000_0000;
        end else begin
            // Écrire quand les deux canaux ont reçu leurs données
            if (write_addr_received && write_data_received && !s_axi_bvalid) begin
                // Adresse valide ? (0x00, 0x04, 0x08, 0x0C)
                if (write_addr[3:2] <= 2'b11) begin
                    // Appliquer les byte strobes
                    if (s_axi_wstrb[0]) registers[write_addr[3:2]][7:0]   <= s_axi_wdata[7:0];
                    if (s_axi_wstrb[1]) registers[write_addr[3:2]][15:8]  <= s_axi_wdata[15:8];
                    if (s_axi_wstrb[2]) registers[write_addr[3:2]][23:16] <= s_axi_wdata[23:16];
                    if (s_axi_wstrb[3]) registers[write_addr[3:2]][31:24] <= s_axi_wdata[31:24];
                end
            end
        end
    end

    // =========================================================================
    // Write Response Channel
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_bvalid <= 1'b0;
            s_axi_bresp <= RESP_OKAY;
        end else begin
            if (write_addr_received && write_data_received && !s_axi_bvalid) begin
                // Prêt à envoyer la réponse
                s_axi_bvalid <= 1'b1;
                s_axi_bresp <= RESP_OKAY;  // Toujours OK pour ce slave simple
            end else if (s_axi_bvalid && s_axi_bready) begin
                // Réponse acceptée
                s_axi_bvalid <= 1'b0;
            end
        end
    end

    // =========================================================================
    // Read Address Channel
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_arready <= 1'b1;
            read_addr <= '0;
        end else begin
            if (s_axi_arvalid && s_axi_arready) begin
                // Handshake réussi
                read_addr <= s_axi_araddr;
                s_axi_arready <= 1'b0;
            end else if (s_axi_rvalid && s_axi_rready) begin
                // Transaction terminée
                s_axi_arready <= 1'b1;
            end
        end
    end

    // =========================================================================
    // Read Data Channel
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_rvalid <= 1'b0;
            s_axi_rdata <= '0;
            s_axi_rresp <= RESP_OKAY;
        end else begin
            if (s_axi_arvalid && s_axi_arready) begin
                // Adresse reçue : préparer les données
                s_axi_rvalid <= 1'b1;
                s_axi_rresp <= RESP_OKAY;
                // Lire le bon registre
                case (s_axi_araddr[3:2])
                    2'b00: s_axi_rdata <= registers[0];
                    2'b01: s_axi_rdata <= registers[1];
                    2'b10: s_axi_rdata <= registers[2];
                    2'b11: s_axi_rdata <= registers[3];
                endcase
            end else if (s_axi_rvalid && s_axi_rready) begin
                // Données acceptées
                s_axi_rvalid <= 1'b0;
            end
        end
    end

endmodule
