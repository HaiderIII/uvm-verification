// ============================================================================
// NoC Router - Routeur 5 ports avec routage XY (version simplifiée pour Icarus)
// ============================================================================
// Compatible avec Icarus Verilog - pas de package externe
// ============================================================================

module noc_router #(
    parameter PACKET_WIDTH = 32,
    parameter ROUTER_X = 0,
    parameter ROUTER_Y = 0
) (
    input  logic clk,
    input  logic rst_n,

    // 5 ports: data_in[0..4], valid_in[0..4], ready_out[0..4]
    //          data_out[0..4], valid_out[0..4], ready_in[0..4]
    // Port 0=NORTH, 1=EAST, 2=SOUTH, 3=WEST, 4=LOCAL

    input  logic [PACKET_WIDTH-1:0] data_in  [0:4],
    input  logic                    valid_in [0:4],
    output logic                    ready_out[0:4],

    output logic [PACKET_WIDTH-1:0] data_out  [0:4],
    output logic                    valid_out [0:4],
    input  logic                    ready_in  [0:4]
);

    // =========================================================================
    // Constantes de direction
    // =========================================================================
    localparam DIR_NORTH = 3'd0;
    localparam DIR_EAST  = 3'd1;
    localparam DIR_SOUTH = 3'd2;
    localparam DIR_WEST  = 3'd3;
    localparam DIR_LOCAL = 3'd4;

    // =========================================================================
    // Extraction des champs du paquet
    // =========================================================================
    // Format: [31:28]=dst_x, [27:24]=dst_y, [23:20]=src_x, [19:16]=src_y, [15:0]=payload

    function automatic [3:0] get_dst_x(input [PACKET_WIDTH-1:0] pkt);
        return pkt[31:28];
    endfunction

    function automatic [3:0] get_dst_y(input [PACKET_WIDTH-1:0] pkt);
        return pkt[27:24];
    endfunction

    // =========================================================================
    // Fonction de routage XY
    // =========================================================================
    function automatic [2:0] compute_direction(
        input [3:0] dst_x,
        input [3:0] dst_y
    );
        if (dst_x > ROUTER_X)
            return DIR_EAST;
        else if (dst_x < ROUTER_X)
            return DIR_WEST;
        else if (dst_y > ROUTER_Y)
            return DIR_SOUTH;
        else if (dst_y < ROUTER_Y)
            return DIR_NORTH;
        else
            return DIR_LOCAL;
    endfunction

    // =========================================================================
    // Calcul des directions pour chaque port d'entrée
    // =========================================================================
    logic [2:0] dir [0:4];

    always_comb begin
        for (int i = 0; i < 5; i++) begin
            dir[i] = compute_direction(get_dst_x(data_in[i]), get_dst_y(data_in[i]));
        end
    end

    // =========================================================================
    // Crossbar combinatoire - priorité: LOCAL(4) > NORTH(0) > EAST(1) > SOUTH(2) > WEST(3)
    // =========================================================================

    always_comb begin
        // Valeurs par défaut
        for (int i = 0; i < 5; i++) begin
            data_out[i]  = '0;
            valid_out[i] = 1'b0;
            ready_out[i] = 1'b0;
        end

        // Route LOCAL input (priorité la plus haute)
        if (valid_in[4]) begin
            data_out[dir[4]]  = data_in[4];
            valid_out[dir[4]] = 1'b1;
            ready_out[4]      = ready_in[dir[4]];
        end

        // Route NORTH input
        if (valid_in[0] && !valid_out[dir[0]]) begin
            data_out[dir[0]]  = data_in[0];
            valid_out[dir[0]] = 1'b1;
            ready_out[0]      = ready_in[dir[0]];
        end

        // Route EAST input
        if (valid_in[1] && !valid_out[dir[1]]) begin
            data_out[dir[1]]  = data_in[1];
            valid_out[dir[1]] = 1'b1;
            ready_out[1]      = ready_in[dir[1]];
        end

        // Route SOUTH input
        if (valid_in[2] && !valid_out[dir[2]]) begin
            data_out[dir[2]]  = data_in[2];
            valid_out[dir[2]] = 1'b1;
            ready_out[2]      = ready_in[dir[2]];
        end

        // Route WEST input
        if (valid_in[3] && !valid_out[dir[3]]) begin
            data_out[dir[3]]  = data_in[3];
            valid_out[dir[3]] = 1'b1;
            ready_out[3]      = ready_in[dir[3]];
        end
    end

endmodule
