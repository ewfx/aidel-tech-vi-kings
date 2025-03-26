// client/src/components/EntityNetworkViz.tsx
import React, { useEffect, useRef, useState } from 'react';
import {
    Text, Paper, Group, Flex, ThemeIcon,
    Badge, Loader, Alert, Center, Box,
    Title, Card, Tooltip, useMantineTheme,
    Button, ActionIcon, Collapse
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
    IconNetwork, IconAlertCircle, IconRefresh,
    IconUser, IconBuilding, IconArrowsExchange,
    IconBoxMultiple, IconShield, IconPlus,
    IconMinus, IconZoomIn, IconZoomOut, IconFocus
} from '@tabler/icons-react';
import { API_URL } from '../api/constants';
import * as d3 from 'd3';

interface EntityNetworkVizProps {
    transactionId: string;
    focusEntityName?: string;
}

interface NetworkNode {
    id: string;
    label: string;
    type: 'Person' | 'Organization' | 'Transaction';
    risk?: number;
}

interface NetworkLink {
    source: string;
    target: string;
    label: string;
}

interface NetworkData {
    nodes: NetworkNode[];
    links: NetworkLink[];
}

const EntityNetworkViz: React.FC<EntityNetworkVizProps> = ({ transactionId, focusEntityName }) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [networkData, setNetworkData] = useState<NetworkData | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const svgRef = useRef<SVGSVGElement | null>(null);
    const [expanded, { toggle }] = useDisclosure(true);
    const theme = useMantineTheme();

    // Simulation state
    const [zoomLevel, setZoomLevel] = useState(1);
    const simulationRef = useRef<any>(null);

    useEffect(() => {
        if (expanded) {
            fetchNetworkData();
        }
    }, [transactionId, expanded, focusEntityName]);

    const fetchNetworkData = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch data from the API
            const response = await fetch(`${API_URL}/transaction/${transactionId}/network`);

            if (!response.ok) {
                throw new Error(`Failed to fetch network data: ${response.statusText}`);
            }

            const data = await response.json();
            setNetworkData(data);

            // Schedule the visualization to be created after the component renders
            setTimeout(() => {
                if (containerRef.current && data) {
                    createVisualization(data);
                }
            }, 100);
        } catch (error) {
            console.error('Error fetching network data:', error);
            setError(error instanceof Error ? error.message : 'Unknown error occurred');

            // If the network endpoint isn't implemented yet, create sample data 
            // This is for demonstration purposes
            const sampleData = createSampleData();
            setNetworkData(sampleData);

            // Schedule the visualization to be created with sample data
            setTimeout(() => {
                if (containerRef.current && sampleData) {
                    createVisualization(sampleData);
                }
            }, 100);
        } finally {
            setLoading(false);
        }
    };

    const createSampleData = (): NetworkData => {
        // Create sample network data for demonstration
        const nodes: NetworkNode[] = [
            { id: 'txn1', label: transactionId, type: 'Transaction' },
            { id: 'org1', label: 'Global Horizons LLC', type: 'Organization', risk: 0.7 },
            { id: 'org2', label: 'Bright Future Nonprofit', type: 'Organization', risk: 0.4 },
            { id: 'person1', label: 'Ali Al-Mansoori', type: 'Person', risk: 0.8 },
            { id: 'org3', label: 'Quantum Holdings Ltd', type: 'Organization', risk: 0.9 },
        ];

        const links: NetworkLink[] = [
            { source: 'org1', target: 'txn1', label: 'sender' },
            { source: 'org2', target: 'txn1', label: 'receiver' },
            { source: 'person1', target: 'org1', label: 'director' },
            { source: 'org3', target: 'txn1', label: 'intermediary' },
            { source: 'person1', target: 'org3', label: 'owner' },
        ];

        return { nodes, links };
    };

    const createVisualization = (data: NetworkData) => {
        if (!containerRef.current) return;

        // Clear previous visualization
        if (svgRef.current) {
            svgRef.current.remove();
        }

        // Get container dimensions
        const containerWidth = containerRef.current.clientWidth;
        const containerHeight = 500;

        // Create SVG element
        const svg = d3.select(containerRef.current)
            .append('svg')
            .attr('width', containerWidth)
            .attr('height', containerHeight)
            .attr('viewBox', [0, 0, containerWidth, containerHeight])
            .attr('style', 'max-width: 100%; height: auto;');

        svgRef.current = svg.node();

        // Create tooltip
        const tooltip = d3.select(containerRef.current)
            .append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('padding', '8px')
            .style('background', 'white')
            .style('border-radius', '4px')
            .style('box-shadow', '0 0 10px rgba(0,0,0,0.1)')
            .style('pointer-events', 'none')
            .style('z-index', 999);

        // Create a zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
                setZoomLevel(event.transform.k);
            });

        svg.call(zoom as any);

        // Create container group for zoom
        const g = svg.append('g');

        // Define color scale based on node type
        const getNodeColor = (node: NetworkNode) => {
            if (node.type === 'Transaction') return theme.colors.blue[6];
            if (node.type === 'Organization') {
                if (node.risk !== undefined) {
                    if (node.risk >= 0.7) return theme.colors.red[6];
                    if (node.risk >= 0.4) return theme.colors.orange[6];
                    return theme.colors.green[6];
                }
                return theme.colors.indigo[6];
            }
            if (node.type === 'Person') {
                if (node.risk !== undefined) {
                    if (node.risk >= 0.7) return theme.colors.red[6];
                    if (node.risk >= 0.4) return theme.colors.orange[6];
                    return theme.colors.green[6];
                }
                return theme.colors.violet[6];
            }
            return theme.colors.gray[6];
        };

        // Define node size based on type
        const getNodeRadius = (node: NetworkNode) => {
            if (node.type === 'Transaction') return 30;
            if (node.type === 'Organization') return 25;
            if (node.type === 'Person') return 20;
            return 15;
        };

        // Define link stroke width based on relationship importance
        const getLinkStrokeWidth = (link: NetworkLink) => {
            if (link.label === 'sender' || link.label === 'receiver') return 3;
            if (link.label === 'director' || link.label === 'owner') return 2;
            return 1.5;
        };

        // Define link stroke color based on relationship type
        const getLinkColor = (link: NetworkLink) => {
            if (link.label === 'sender') return theme.colors.blue[4];
            if (link.label === 'receiver') return theme.colors.green[4];
            if (link.label === 'intermediary') return theme.colors.orange[4];
            if (link.label === 'director' || link.label === 'owner') return theme.colors.indigo[4];
            return theme.colors.gray[4];
        };

        // Create links (edges)
        const links = g.selectAll('.link')
            .data(data.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', d => getLinkColor(d))
            .attr('stroke-width', d => getLinkStrokeWidth(d))
            .attr('stroke-opacity', 0.6);

        // Create link labels
        const linkLabels = g.selectAll('.link-label')
            .data(data.links)
            .enter()
            .append('text')
            .attr('class', 'link-label')
            .attr('font-size', 10)
            .attr('text-anchor', 'middle')
            .attr('dy', -5)
            .text(d => d.label)
            .attr('fill', theme.colors.gray[7])
            .attr('pointer-events', 'none')
            .attr('opacity', 0.8);

        // Create nodes
        const nodes = g.selectAll('.node')
            .data(data.nodes)
            .enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => getNodeRadius(d))
            .attr('fill', d => getNodeColor(d))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .on('mouseover', (event, d) => {
                tooltip.transition()
                    .duration(200)
                    .style('opacity', 0.9);
                tooltip.html(`
          <div style="font-weight: bold;">${d.label}</div>
          <div>Type: ${d.type}</div>
          ${d.risk !== undefined ? `<div>Risk: ${Math.round(d.risk * 100)}%</div>` : ''}
        `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', () => {
                tooltip.transition()
                    .duration(500)
                    .style('opacity', 0);
            });

        // Add node labels
        const nodeLabels = g.selectAll('.node-label')
            .data(data.nodes)
            .enter()
            .append('text')
            .attr('class', 'node-label')
            .attr('text-anchor', 'middle')
            .attr('dy', d => getNodeRadius(d) + 15)
            .text(d => d.label.length > 20 ? d.label.substring(0, 17) + '...' : d.label)
            .attr('font-size', 12)
            .attr('fill', theme.colors.dark[7])
            .attr('pointer-events', 'none');

        // Add node icons
        const nodeIcons = g.selectAll('.node-icon')
            .data(data.nodes)
            .enter()
            .append('text')
            .attr('class', 'node-icon')
            .attr('text-anchor', 'middle')
            .attr('dy', 5)
            .html(d => {
                if (d.type === 'Transaction') return '💱';
                if (d.type === 'Organization') return '🏢';
                if (d.type === 'Person') return '👤';
                return '📄';
            })
            .attr('font-size', 16)
            .attr('pointer-events', 'none');

        // Create force simulation
        const simulation = d3.forceSimulation(data.nodes as d3.SimulationNodeDatum[])
            .force('link', d3.forceLink(data.links)
                .id((d: any) => d.id)
                .distance(150))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(containerWidth / 2, containerHeight / 2))
            .force('collision', d3.forceCollide().radius(d => (d as NetworkNode).type === 'Transaction' ? 60 : 40));

        simulationRef.current = simulation;

        // Update positions on simulation tick
        simulation.on('tick', () => {
            links
                .attr('x1', d => (d.source as any).x)
                .attr('y1', d => (d.source as any).y)
                .attr('x2', d => (d.target as any).x)
                .attr('y2', d => (d.target as any).y);

            linkLabels
                .attr('x', d => ((d.source as any).x + (d.target as any).x) / 2)
                .attr('y', d => ((d.source as any).y + (d.target as any).y) / 2);

            nodes
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            nodeLabels
                .attr('x', d => d.x)
                .attr('y', d => d.y);

            nodeIcons
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        });

        // If there's a focused entity, highlight it
        if (focusEntityName) {
            const focusNode = data.nodes.find(node => node.label === focusEntityName);
            if (focusNode) {
                // Highlight the node
                nodes.filter(d => d.id === focusNode.id)
                    .attr('stroke', theme.colors.yellow[5])
                    .attr('stroke-width', 4);

                // Center the view on this node
                setTimeout(() => {
                    if (svgRef.current) {
                        const transform = d3.zoomIdentity
                            .translate(containerWidth / 2, containerHeight / 2)
                            .scale(1.2)
                            .translate(-(focusNode.x || 0), -(focusNode.y || 0));

                        d3.select(svgRef.current).transition().duration(750)
                            .call((zoom as any).transform, transform);
                    }
                }, 500);
            }
        }
    };

    const handleZoom = (direction: 'in' | 'out') => {
        if (!svgRef.current) return;

        const svg = d3.select(svgRef.current);
        const zoom = d3.zoom().on('zoom', null);

        const currentTransform = d3.zoomTransform(svg.node() as Element);
        let newScale = direction === 'in' ? currentTransform.k * 1.3 : currentTransform.k / 1.3;

        // Limit scale
        newScale = Math.max(0.1, Math.min(4, newScale));

        const transform = d3.zoomIdentity
            .translate(currentTransform.x, currentTransform.y)
            .scale(newScale);

        svg.transition().duration(300)
            .call((zoom as any).transform, transform);

        setZoomLevel(newScale);
    };

    const handleReset = () => {
        if (!svgRef.current || !containerRef.current) return;

        const svg = d3.select(svgRef.current);
        const zoom = d3.zoom().on('zoom', null);

        const containerWidth = containerRef.current.clientWidth;
        const containerHeight = 500;

        const transform = d3.zoomIdentity
            .translate(containerWidth / 2, containerHeight / 2)
            .scale(1);

        svg.transition().duration(750)
            .call((zoom as any).transform, transform);

        setZoomLevel(1);

        // Restart simulation
        if (simulationRef.current) {
            simulationRef.current.alpha(0.3).restart();
        }
    };

    return (
        <Card withBorder p="lg" radius="md" shadow="sm">
            <Flex justify="space-between" align="center" mb="md">
                <Flex align="center" gap="md">
                    <ThemeIcon size="lg" radius="md" color="blue" variant="light">
                        <IconNetwork size={20} />
                    </ThemeIcon>
                    <Title order={5}>Entity Network</Title>
                </Flex>

                <Group>
                    <Tooltip label={expanded ? "Collapse" : "Expand"}>
                        <ActionIcon onClick={toggle} variant="light">
                            {expanded ? <IconMinus size={16} /> : <IconPlus size={16} />}
                        </ActionIcon>
                    </Tooltip>

                    <ActionIcon variant="light" onClick={fetchNetworkData}>
                        <IconRefresh size={16} />
                    </ActionIcon>
                </Group>
            </Flex>

            <Collapse in={expanded}>
                {loading ? (
                    <Center p="xl">
                        <Flex direction="column" align="center" gap="md">
                            <Loader size="md" />
                            <Text c="dimmed">Loading network data...</Text>
                        </Flex>
                    </Center>
                ) : error ? (
                    <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red" radius="md">
                        <Text size="sm">{error}</Text>
                    </Alert>
                ) : (
                    <>
                        <Paper withBorder radius="md" style={{ overflow: 'hidden' }}>
                            <Box>
                                <Flex p="xs" justify="space-between" bg={theme.colors.gray[0]}>
                                    <Group>
                                        <Badge color="blue">
                                            {networkData?.nodes.length || 0} Entities
                                        </Badge>
                                        <Badge color="indigo">
                                            {networkData?.links.length || 0} Connections
                                        </Badge>
                                    </Group>

                                    <Group>
                                        <Tooltip label="Zoom in">
                                            <ActionIcon onClick={() => handleZoom('in')} disabled={zoomLevel >= 4}>
                                                <IconZoomIn size={16} />
                                            </ActionIcon>
                                        </Tooltip>
                                        <Badge variant="outline">
                                            {Math.round(zoomLevel * 100)}%
                                        </Badge>
                                        <Tooltip label="Zoom out">
                                            <ActionIcon onClick={() => handleZoom('out')} disabled={zoomLevel <= 0.1}>
                                                <IconZoomOut size={16} />
                                            </ActionIcon>
                                        </Tooltip>
                                        <Tooltip label="Reset view">
                                            <ActionIcon onClick={handleReset}>
                                                <IconFocus size={16} />
                                            </ActionIcon>
                                        </Tooltip>
                                    </Group>
                                </Flex>

                                <Box ref={containerRef} style={{ width: '100%', height: '500px', position: 'relative' }} />
                            </Box>
                        </Paper>

                    </>
                )}
            </Collapse>
        </Card>
    );
};

export default EntityNetworkViz;