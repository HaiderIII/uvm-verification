// ============================================================================
// NoC Router - Routeur 5 ports avec routage XY (version simplifiée)
// ============================================================================
// Version combinatoire pour projet pédagogique
// ============================================================================

module noc_router
    import noc_pkg::*;
#(
    parameter ROUTER_X = 0,
    parameter ROUTER_Y = 0
) (
    input  logic clk,
    input  logic rst_n,

    // Port LOCAL
    input  logic [PACKET_WIDTH-1:0]  local_in_tdata,
    input  logic                     local_in_tvalid,
    output logic                     local_in_tready,
    input  logic                     local_in_tlast,

    output logic [PACKET_WIDTH-1:0]  local_out_tdata,
    output logic                     local_out_tvalid,
    input  logic                     local_out_tready,
    output logic                     local_out_tlast,

    // Port NORTH
    input  logic [PACKET_WIDTH-1:0]  north_in_tdata,
    input  logic                     north_in_tvalid,
    output logic                     north_in_tready,
    input  logic                     north_in_tlast,

    output logic [PACKET_WIDTH-1:0]  north_out_tdata,
    output logic                     north_out_tvalid,
    input  logic                     north_out_tready,
    output logic                     north_out_tlast,

    // Port SOUTH
    input  logic [PACKET_WIDTH-1:0]  south_in_tdata,
    input  logic                     south_in_tvalid,
    output logic                     south_in_tready,
    input  logic                     south_in_tlast,

    output logic [PACKET_WIDTH-1:0]  south_out_tdata,
    output logic                     south_out_tvalid,
    input  logic                     south_out_tready,
    output logic                     south_out_tlast,

    // Port EAST
    input  logic [PACKET_WIDTH-1:0]  east_in_tdata,
    input  logic                     east_in_tvalid,
    output logic                     east_in_tready,
    input  logic                     east_in_tlast,

    output logic [PACKET_WIDTH-1:0]  east_out_tdata,
    output logic                     east_out_tvalid,
    input  logic                     east_out_tready,
    output logic                     east_out_tlast,

    // Port WEST
    input  logic [PACKET_WIDTH-1:0]  west_in_tdata,
    input  logic                     west_in_tvalid,
    output logic                     west_in_tready,
    input  logic                     west_in_tlast,

    output logic [PACKET_WIDTH-1:0]  west_out_tdata,
    output logic                     west_out_tvalid,
    input  logic                     west_out_tready,
    output logic                     west_out_tlast
);

    // =========================================================================
    // Fonction de routage XY
    // =========================================================================
    function automatic direction_t compute_direction(
        input logic [3:0] dst_x,
        input logic [3:0] dst_y
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
    // Calcul des directions
    // =========================================================================
    direction_t local_dir, north_dir, south_dir, east_dir, west_dir;

    always_comb begin
        local_dir = compute_direction(get_dst_x(local_in_tdata), get_dst_y(local_in_tdata));
        north_dir = compute_direction(get_dst_x(north_in_tdata), get_dst_y(north_in_tdata));
        south_dir = compute_direction(get_dst_x(south_in_tdata), get_dst_y(south_in_tdata));
        east_dir  = compute_direction(get_dst_x(east_in_tdata),  get_dst_y(east_in_tdata));
        west_dir  = compute_direction(get_dst_x(west_in_tdata),  get_dst_y(west_in_tdata));
    end

    // =========================================================================
    // Crossbar combinatoire - priorité: Local > North > South > East > West
    // =========================================================================

    always_comb begin
        // Valeurs par défaut - tout à zéro
        local_out_tdata  = '0;
        local_out_tvalid = 1'b0;
        local_out_tlast  = 1'b0;

        north_out_tdata  = '0;
        north_out_tvalid = 1'b0;
        north_out_tlast  = 1'b0;

        south_out_tdata  = '0;
        south_out_tvalid = 1'b0;
        south_out_tlast  = 1'b0;

        east_out_tdata   = '0;
        east_out_tvalid  = 1'b0;
        east_out_tlast   = 1'b0;

        west_out_tdata   = '0;
        west_out_tvalid  = 1'b0;
        west_out_tlast   = 1'b0;

        // Ready par défaut
        local_in_tready = 1'b0;
        north_in_tready = 1'b0;
        south_in_tready = 1'b0;
        east_in_tready  = 1'b0;
        west_in_tready  = 1'b0;

        // =====================================================================
        // Route LOCAL input
        // =====================================================================
        if (local_in_tvalid) begin
            case (local_dir)
                DIR_LOCAL: begin
                    local_out_tdata  = local_in_tdata;
                    local_out_tvalid = 1'b1;
                    local_out_tlast  = local_in_tlast;
                    local_in_tready  = local_out_tready;
                end
                DIR_NORTH: begin
                    north_out_tdata  = local_in_tdata;
                    north_out_tvalid = 1'b1;
                    north_out_tlast  = local_in_tlast;
                    local_in_tready  = north_out_tready;
                end
                DIR_SOUTH: begin
                    south_out_tdata  = local_in_tdata;
                    south_out_tvalid = 1'b1;
                    south_out_tlast  = local_in_tlast;
                    local_in_tready  = south_out_tready;
                end
                DIR_EAST: begin
                    east_out_tdata   = local_in_tdata;
                    east_out_tvalid  = 1'b1;
                    east_out_tlast   = local_in_tlast;
                    local_in_tready  = east_out_tready;
                end
                DIR_WEST: begin
                    west_out_tdata   = local_in_tdata;
                    west_out_tvalid  = 1'b1;
                    west_out_tlast   = local_in_tlast;
                    local_in_tready  = west_out_tready;
                end
                default: local_in_tready = 1'b1;
            endcase
        end

        // =====================================================================
        // Route NORTH input (si pas de conflit)
        // =====================================================================
        if (north_in_tvalid) begin
            case (north_dir)
                DIR_LOCAL: if (!local_out_tvalid) begin
                    local_out_tdata  = north_in_tdata;
                    local_out_tvalid = 1'b1;
                    local_out_tlast  = north_in_tlast;
                    north_in_tready  = local_out_tready;
                end
                DIR_SOUTH: if (!south_out_tvalid) begin
                    south_out_tdata  = north_in_tdata;
                    south_out_tvalid = 1'b1;
                    south_out_tlast  = north_in_tlast;
                    north_in_tready  = south_out_tready;
                end
                DIR_EAST: if (!east_out_tvalid) begin
                    east_out_tdata   = north_in_tdata;
                    east_out_tvalid  = 1'b1;
                    east_out_tlast   = north_in_tlast;
                    north_in_tready  = east_out_tready;
                end
                DIR_WEST: if (!west_out_tvalid) begin
                    west_out_tdata   = north_in_tdata;
                    west_out_tvalid  = 1'b1;
                    west_out_tlast   = north_in_tlast;
                    north_in_tready  = west_out_tready;
                end
                default: north_in_tready = 1'b1;
            endcase
        end

        // =====================================================================
        // Route SOUTH input
        // =====================================================================
        if (south_in_tvalid) begin
            case (south_dir)
                DIR_LOCAL: if (!local_out_tvalid) begin
                    local_out_tdata  = south_in_tdata;
                    local_out_tvalid = 1'b1;
                    local_out_tlast  = south_in_tlast;
                    south_in_tready  = local_out_tready;
                end
                DIR_NORTH: if (!north_out_tvalid) begin
                    north_out_tdata  = south_in_tdata;
                    north_out_tvalid = 1'b1;
                    north_out_tlast  = south_in_tlast;
                    south_in_tready  = north_out_tready;
                end
                DIR_EAST: if (!east_out_tvalid) begin
                    east_out_tdata   = south_in_tdata;
                    east_out_tvalid  = 1'b1;
                    east_out_tlast   = south_in_tlast;
                    south_in_tready  = east_out_tready;
                end
                DIR_WEST: if (!west_out_tvalid) begin
                    west_out_tdata   = south_in_tdata;
                    west_out_tvalid  = 1'b1;
                    west_out_tlast   = south_in_tlast;
                    south_in_tready  = west_out_tready;
                end
                default: south_in_tready = 1'b1;
            endcase
        end

        // =====================================================================
        // Route EAST input
        // =====================================================================
        if (east_in_tvalid) begin
            case (east_dir)
                DIR_LOCAL: if (!local_out_tvalid) begin
                    local_out_tdata  = east_in_tdata;
                    local_out_tvalid = 1'b1;
                    local_out_tlast  = east_in_tlast;
                    east_in_tready   = local_out_tready;
                end
                DIR_NORTH: if (!north_out_tvalid) begin
                    north_out_tdata  = east_in_tdata;
                    north_out_tvalid = 1'b1;
                    north_out_tlast  = east_in_tlast;
                    east_in_tready   = north_out_tready;
                end
                DIR_SOUTH: if (!south_out_tvalid) begin
                    south_out_tdata  = east_in_tdata;
                    south_out_tvalid = 1'b1;
                    south_out_tlast  = east_in_tlast;
                    east_in_tready   = south_out_tready;
                end
                DIR_WEST: if (!west_out_tvalid) begin
                    west_out_tdata   = east_in_tdata;
                    west_out_tvalid  = 1'b1;
                    west_out_tlast   = east_in_tlast;
                    east_in_tready   = west_out_tready;
                end
                default: east_in_tready = 1'b1;
            endcase
        end

        // =====================================================================
        // Route WEST input
        // =====================================================================
        if (west_in_tvalid) begin
            case (west_dir)
                DIR_LOCAL: if (!local_out_tvalid) begin
                    local_out_tdata  = west_in_tdata;
                    local_out_tvalid = 1'b1;
                    local_out_tlast  = west_in_tlast;
                    west_in_tready   = local_out_tready;
                end
                DIR_NORTH: if (!north_out_tvalid) begin
                    north_out_tdata  = west_in_tdata;
                    north_out_tvalid = 1'b1;
                    north_out_tlast  = west_in_tlast;
                    west_in_tready   = north_out_tready;
                end
                DIR_SOUTH: if (!south_out_tvalid) begin
                    south_out_tdata  = west_in_tdata;
                    south_out_tvalid = 1'b1;
                    south_out_tlast  = west_in_tlast;
                    west_in_tready   = south_out_tready;
                end
                DIR_EAST: if (!east_out_tvalid) begin
                    east_out_tdata   = west_in_tdata;
                    east_out_tvalid  = 1'b1;
                    east_out_tlast   = west_in_tlast;
                    west_in_tready   = east_out_tready;
                end
                default: west_in_tready = 1'b1;
            endcase
        end
    end

endmodule
